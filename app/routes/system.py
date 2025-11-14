from flask import Blueprint, jsonify
import psutil

system_bp = Blueprint('system', __name__)

@system_bp.route('/')
def index():
    return "<h1>System Metrics</h1>"

@system_bp.route('/metrics')
def metrics():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    return jsonify({
        'cpu_percent': cpu,
        'ram_percent': ram,
        'disk_percent': disk
    })
