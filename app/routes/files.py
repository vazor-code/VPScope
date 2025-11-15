from flask import Blueprint, jsonify, request, send_from_directory, send_file, render_template
from flask_login import login_required, current_user
from app.utils.file_utils import list_dir, save_upload, delete_file, make_dir
from app import socketio  # Import socketio from __init__.py
import os
from urllib.parse import unquote

files_bp = Blueprint('files', __name__)

def get_drives():
    """Returns list of available drives in the system"""
    drives = []
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f'{letter}:'
        if os.path.exists(drive):
            drives.append(drive)
    return drives

def normalize_path(path):
    """Normalizes path for proper work with Windows drives"""
    if os.name == 'nt':  # Windows
        # If path is just drive letter (e.g., "D:"), convert to "D:\"
        if len(path) == 2 and path[1] == ':' and path[0].isalpha():
            return f"{path}\\"
        # If path ends with ":", add "\" (e.g., "D:" -> "D:\")
        elif path.endswith(':') and len(path) == 2:
            return f"{path}\\"
    return os.path.normpath(path)

def emit_file_change_event(path):
    """Function to send file change event via WebSocket"""
    # Emit to user's room for security
    room = f"user_{current_user.id}" if current_user.is_authenticated else None
    if room:
        socketio.emit('file_change', {'path': path}, room=room, namespace='/file_updates')
    else:
        socketio.emit('file_change', {'path': path}, namespace='/file_updates')

def safe_path(base_dir, path):
    """Secure path joining to prevent directory traversal"""
    # Normalize and join
    full_path = os.path.normpath(os.path.join(base_dir, path.lstrip('/')))
    # Check if it's within base_dir
    if not full_path.startswith(base_dir):
        raise ValueError("Invalid path: directory traversal attempt")
    return full_path

@files_bp.route('/')
@login_required
def index():
    return render_template('files.html')

@files_bp.route('/list', methods=['GET'])
@login_required
def list_directory():
    path = request.args.get('path', '.')
    base_dir = os.getcwd()  # Limit to current working directory for security
    try:
        # Decode URL-encoded path
        path = unquote(path)
        # Normalize path
        normalized_path = normalize_path(path)

        # Handle root path
        if normalized_path in ('/', '.', ''):
            safe_full_path = base_dir
        # Allow drive letters for browsing (read-only)
        elif len(normalized_path) == 2 and normalized_path[1] == ':' and normalized_path[0].isalpha() and normalized_path in get_drives():
            safe_full_path = normalized_path
        else:
            safe_full_path = safe_path(base_dir, normalized_path)

        result = list_dir(safe_full_path)
        # Add info about available drives
        result['drives'] = get_drives()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    files = request.files.getlist('file')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No selected file'}), 400

    base_dir = os.getcwd()
    try:
        path = request.form.get('path', '.')
        # Decode URL-encoded path
        path = unquote(path)
        # Normalize path
        normalized_path = normalize_path(path)
        # Only allow upload within base_dir
        safe_path_dir = safe_path(base_dir, normalized_path)

        uploaded_files = []
        for file in files:
            if file.filename:  # Check if file has name
                # Save file with original name
                filename = file.filename
                filepath = os.path.join(safe_path_dir, filename)

                # If file with such name exists, add number
                counter = 1
                original_filename = filename
                while os.path.exists(filepath):
                    name, ext = os.path.splitext(original_filename)
                    filename = f"{name} ({counter}){ext}"
                    filepath = os.path.join(safe_path_dir, filename)
                    counter += 1

                # Save file
                file.save(filepath)
                uploaded_files.append(filename)

        # Send file change event
        emit_file_change_event(safe_path_dir)

        return jsonify({
            'message': 'Files uploaded successfully',
            'uploaded_files': uploaded_files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/view/<path:filename>')
@login_required
def view_file(filename):
    """Route for viewing files (not for downloading)"""
    base_dir = os.getcwd()
    try:
        # Normalize path
        filename = normalize_path(filename)
        # Allow viewing from drives or within base_dir
        if len(filename) == 2 and filename[1] == ':' and filename[0].isalpha() and filename in get_drives():
            safe_full_path = filename
        else:
            safe_full_path = safe_path(base_dir, filename)

        # For Windows full path (e.g., D:\path\to\file.pdf)
        if ':' in filename and filename[1] == os.sep and filename[0].isalpha():
            # This is path in format D:\filename, use it directly but validate
            directory = os.path.dirname(safe_full_path)
            filename_only = os.path.basename(safe_full_path)
            return send_from_directory(directory, filename_only, as_attachment=False)
        else:
            # Relative path, handle as usual
            directory = os.path.dirname(safe_full_path)
            filename_only = os.path.basename(safe_full_path)
            return send_from_directory(directory, filename_only, as_attachment=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/download/<path:filename>')
@login_required
def download_file(filename):
    """Route for downloading files"""
    base_dir = os.getcwd()
    try:
        # Normalize path
        filename = normalize_path(filename)
        # Allow downloading from drives or within base_dir
        if len(filename) == 2 and filename[1] == ':' and filename[0].isalpha() and filename in get_drives():
            safe_full_path = filename
        else:
            safe_full_path = safe_path(base_dir, filename)

        # For Windows full path (e.g., D:\path\to\file.pdf)
        if ':' in filename and filename[1] == os.sep and filename[0].isalpha():
            # This is path in format D:\filename, use it directly but validate
            directory = os.path.dirname(safe_full_path)
            filename_only = os.path.basename(safe_full_path)
            return send_from_directory(directory, filename_only, as_attachment=True)
        else:
            # Relative path, handle as usual
            directory = os.path.dirname(safe_full_path)
            filename_only = os.path.basename(safe_full_path)
            return send_from_directory(directory, filename_only, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/delete', methods=['POST'])
@login_required
def delete_item():
    path = request.json.get('path')
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    base_dir = os.getcwd()
    try:
        # Normalize path
        normalized_path = normalize_path(path)
        # Only allow delete within base_dir
        safe_full_path = safe_path(base_dir, normalized_path)
        delete_file(safe_full_path)
        # Send file change event
        parent_dir = os.path.dirname(safe_full_path) if os.path.dirname(safe_full_path) else base_dir
        emit_file_change_event(parent_dir)
        return jsonify({'message': 'Item deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/mkdir', methods=['POST'])
@login_required
def create_directory():
    path = request.json.get('path')
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    base_dir = os.getcwd()
    try:
        # Normalize path
        normalized_path = normalize_path(path)
        # Only allow mkdir within base_dir
        safe_full_path = safe_path(base_dir, normalized_path)
        make_dir(safe_full_path)
        # Send file change event
        parent_dir = os.path.dirname(safe_full_path) if os.path.dirname(safe_full_path) else base_dir
        emit_file_change_event(parent_dir)
        return jsonify({'message': 'Directory created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/read', methods=['GET'])
@login_required
def read_file():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'Path is required'}), 400

    base_dir = os.getcwd()
    try:
        # Normalize path
        normalized_path = normalize_path(path)
        # Allow reading from drives or within base_dir
        if len(normalized_path) == 2 and normalized_path[1] == ':' and normalized_path[0].isalpha() and normalized_path in get_drives():
            safe_full_path = normalized_path
        else:
            safe_full_path = safe_path(base_dir, normalized_path)

        with open(safe_full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/write', methods=['POST'])
@login_required
def write_file():
    data = request.json
    path = data.get('path')
    content = data.get('content', '')

    if not path:
        return jsonify({'error': 'Path is required'}), 400

    base_dir = os.getcwd()
    try:
        # Normalize path
        normalized_path = normalize_path(path)
        # Only allow write within base_dir
        safe_full_path = safe_path(base_dir, normalized_path)

        # Create directory if it doesn't exist
        directory = os.path.dirname(safe_full_path)
        if directory and directory != '.' and directory != '' and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(safe_full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Send file change event
        emit_file_change_event(safe_full_path)
        return jsonify({'message': 'File written successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/rename', methods=['POST'])
@login_required
def rename_item():
    data = request.json
    old_path = data.get('old_path')
    new_path = data.get('new_path')
    
    if not old_path or not new_path:
        return jsonify({'error': 'Both old_path and new_path are required'}), 400
    
    base_dir = os.getcwd()
    try:
        # Normalize paths
        old_normalized = normalize_path(old_path)
        new_normalized = normalize_path(new_path)
        safe_old = safe_path(base_dir, old_normalized)
        safe_new = safe_path(base_dir, new_normalized)
        
        os.rename(safe_old, safe_new)
        # Send file change event
        parent_dir = os.path.dirname(safe_old) if os.path.dirname(safe_old) else base_dir
        emit_file_change_event(parent_dir)
        return jsonify({'message': 'Item renamed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/drives', methods=['GET'])
@login_required
def get_available_drives():
    """Returns list of available drives"""
    try:
        drives = get_drives()
        return jsonify({'drives': drives})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
