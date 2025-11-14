import os
from werkzeug.utils import secure_filename

def list_dir(path='.'):
    entries = []
    for name in os.listdir(path):
        full = os.path.join(path, name)
        is_dir = os.path.isdir(full)
        entries.append({
            'name': name,
            'path': full,
            'is_dir': is_dir,
            'size': os.path.getsize(full) if not is_dir else None
        })
    entries.sort(key=lambda x: (not x['is_dir'], x['name']))
    return {'path': os.path.abspath(path), 'entries': entries}

def save_upload(file_storage, target_path='.'):
    filename = secure_filename(file_storage.filename)
    file_storage.save(os.path.join(target_path, filename))
    return filename

def delete_file(path):
    if os.path.isdir(path):
        import shutil
        shutil.rmtree(path)
    else:
        os.remove(path)
    return True

def make_dir(path):
    os.makedirs(path, exist_ok=True)
