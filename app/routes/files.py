from flask import Blueprint, jsonify, request, send_from_directory, send_file
from app.utils.file_utils import list_dir, save_upload, delete_file, make_dir
from app import socketio  # Импортируем socketio из __init__.py
import os

files_bp = Blueprint('files', __name__)

def get_drives():
    """Возвращает список доступных дисков в системе"""
    drives = []
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f'{letter}:'
        if os.path.exists(drive):
            drives.append(drive)
    return drives

def normalize_path(path):
    """Нормализует путь для правильной работы с дисками Windows"""
    if os.name == 'nt':  # Windows
        # Если путь - это просто буква диска (например, "D:"), преобразуем в "D:\"
        if len(path) == 2 and path[1] == ':' and path[0].isalpha():
            return f"{path}\\"
        # Если путь заканчивается на ":", добавляем "\" (например, "D:" -> "D:\")
        elif path.endswith(':') and len(path) == 2:
            return f"{path}\\"
    return os.path.normpath(path)

def emit_file_change_event(path):
    """Функция для отправки события изменения файлов через WebSocket"""
    socketio.emit('file_change', {'path': path}, namespace='/file_updates')

@files_bp.route('/')
def index():
    return "<h1>File Manager API</h1>"

@files_bp.route('/list', methods=['GET'])
def list_directory():
    path = request.args.get('path', '.')
    try:
        # Нормализуем путь
        normalized_path = normalize_path(path)
        result = list_dir(normalized_path)
        # Добавляем информацию о доступных дисках
        result['drives'] = get_drives()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('file')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        path = request.form.get('path', '.')
        # Нормализуем путь
        path = normalize_path(path)
        
        uploaded_files = []
        for file in files:
            if file.filename:  # Проверяем, что файл имеет имя
                # Сохраняем файл с оригинальным именем
                filename = file.filename
                filepath = os.path.join(path, filename)
                
                # Если файл с таким именем уже существует, добавляем номер
                counter = 1
                original_filename = filename
                while os.path.exists(filepath):
                    name, ext = os.path.splitext(original_filename)
                    filename = f"{name} ({counter}){ext}"
                    filepath = os.path.join(path, filename)
                    counter += 1
                
                # Сохраняем файл
                file.save(filepath)
                uploaded_files.append(filename)
        
        # Отправляем событие об изменении файлов
        emit_file_change_event(path)
        
        return jsonify({
            'message': 'Files uploaded successfully',
            'uploaded_files': uploaded_files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/view/<path:filename>')
def view_file(filename):
    """Маршрут для просмотра файлов (не для скачивания)"""
    # Нормализуем путь
    filename = normalize_path(filename)
    
    # Если это полный путь Windows (например, D:\path\to\file.pdf)
    if ':' in filename and filename[1] == os.sep and filename[0].isalpha():
        # Это путь в формате D:\filename, используем его напрямую
        directory = os.path.dirname(filename)
        if directory == '':
            directory = '.'
        filename_only = os.path.basename(filename)
        return send_from_directory(directory, filename_only, as_attachment=False)
    else:
        # Это относительный путь, обрабатываем как обычно
        directory = os.path.dirname(filename)
        if directory == '' or directory == '.':
            directory = '.'
        filename_only = os.path.basename(filename)
        return send_from_directory(directory, filename_only, as_attachment=False)

@files_bp.route('/download/<path:filename>')
def download_file(filename):
    """Маршрут для скачивания файлов"""
    # Нормализуем путь
    filename = normalize_path(filename)
    
    # Если это полный путь Windows (например, D:\path\to\file.pdf)
    if ':' in filename and filename[1] == os.sep and filename[0].isalpha():
        # Это путь в формате D:\filename, используем его напрямую
        directory = os.path.dirname(filename)
        if directory == '':
            directory = '.'
        filename_only = os.path.basename(filename)
        return send_from_directory(directory, filename_only, as_attachment=True)
    else:
        # Это относительный путь, обрабатываем как обычно
        directory = os.path.dirname(filename)
        if directory == '' or directory == '.':
            directory = '.'
        filename_only = os.path.basename(filename)
        return send_from_directory(directory, filename_only, as_attachment=True)

@files_bp.route('/delete', methods=['POST'])
def delete_item():
    path = request.json.get('path')
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    try:
        # Нормализуем путь
        path = normalize_path(path)
        delete_file(path)
        # Отправляем событие об изменении файлов
        parent_dir = os.path.dirname(path) if os.path.dirname(path) else '.'
        emit_file_change_event(parent_dir)
        return jsonify({'message': 'Item deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/mkdir', methods=['POST'])
def create_directory():
    path = request.json.get('path')
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    try:
        # Нормализуем путь
        path = normalize_path(path)
        make_dir(path)
        # Отправляем событие об изменении файлов
        parent_dir = os.path.dirname(path) if os.path.dirname(path) else '.'
        emit_file_change_event(parent_dir)
        return jsonify({'message': 'Directory created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/read', methods=['GET'])
def read_file():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    
    # Нормализуем путь
    path = normalize_path(path)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/write', methods=['POST'])
def write_file():
    data = request.json
    path = data.get('path')
    content = data.get('content', '')
    
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    
    # Нормализуем путь
    path = normalize_path(path)
    
    try:
        # Создаем директорию, если она не существует
        directory = os.path.dirname(path)
        if directory and directory != '.' and directory != '' and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Отправляем событие об изменении файлов
        emit_file_change_event(path)
        return jsonify({'message': 'File written successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/rename', methods=['POST'])
def rename_item():
    data = request.json
    old_path = data.get('old_path')
    new_path = data.get('new_path')
    
    if not old_path or not new_path:
        return jsonify({'error': 'Both old_path and new_path are required'}), 400
    
    # Нормализуем пути
    old_path = normalize_path(old_path)
    new_path = normalize_path(new_path)
    
    try:
        os.rename(old_path, new_path)
        # Отправляем событие об изменении файлов
        parent_dir = os.path.dirname(old_path) if os.path.dirname(old_path) else '.'
        emit_file_change_event(parent_dir)
        return jsonify({'message': 'Item renamed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/drives', methods=['GET'])
def get_available_drives():
    """Возвращает список доступных дисков"""
    try:
        drives = get_drives()
        return jsonify({'drives': drives})
    except Exception as e:
        return jsonify({'error': str(e)}), 500