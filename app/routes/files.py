from flask import Blueprint, jsonify, request, send_file
import os
from werkzeug.utils import secure_filename

files_bp = Blueprint('files', __name__, template_folder='templates')

def list_dir(path):
    entries = []
    for e in os.scandir(path):
        entries.append({'name': e.name, 'is_dir': e.is_dir(), 'path': os.path.abspath(e.path)})
    return {'path': os.path.abspath(path), 'entries': entries}

@files_bp.route('/')
def index():
    return "<h1>File Explorer</h1>"

@files_bp.route('/list')
def list_files_route():
    path = request.args.get('path', '.')
    path = os.path.abspath(path)
    if not os.path.exists(path) or not os.path.isdir(path):
        return jsonify({'error': 'invalid path'}), 400
    return jsonify(list_dir(path))

@files_bp.route('/upload', methods=['POST'])
def upload():
    target = request.form.get('path', '.')
    file_storage = request.files.get('file')
    if not file_storage:
        return jsonify({'error':'No file'}), 400
    target = os.path.abspath(target)
    os.makedirs(target, exist_ok=True)
    filename = secure_filename(file_storage.filename)
    file_storage.save(os.path.join(target, filename))
    return jsonify({'ok': True})

@files_bp.route('/download')
def download():
    path = request.args.get('path')
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        return jsonify({'error':'not found'}),404
    return send_file(path, as_attachment=True)

@files_bp.route('/delete', methods=['POST'])
def delete():
    data = request.get_json(silent=True) or {}
    path = data.get('path')
    if not path: return jsonify({'error':'path required'}),400
    path = os.path.abspath(path)
    if not os.path.exists(path): return jsonify({'error':'not found'}),404
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
    except Exception as e:
        return jsonify({'error':str(e)}),500
    return jsonify({'deleted': True})
