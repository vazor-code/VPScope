from flask import Blueprint, jsonify, request, send_from_directory
from app.utils.file_utils import list_dir, save_upload, delete_file, make_dir
import os

files_bp = Blueprint('files', __name__)

@files_bp.route('/')
def index():
    return "<h1>File Manager API</h1>"

@files_bp.route('/list', methods=['GET'])
def list_directory():
    path = request.args.get('path', '.')
    try:
        return jsonify(list_dir(path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    try:
        save_upload(file, request.form.get('path', '.'))
        return jsonify({'message': 'File uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/delete', methods=['POST'])
def delete_item():
    path = request.json.get('path')
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    try:
        delete_file(path)
        return jsonify({'message': 'Item deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/mkdir', methods=['POST'])
def create_directory():
    path = request.json.get('path')
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    try:
        make_dir(path)
        return jsonify({'message': 'Directory created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory('.', filename, as_attachment=True)
