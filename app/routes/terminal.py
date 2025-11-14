from flask import Blueprint
from .. import socketio
import subprocess

terminal_bp = Blueprint('terminal', __name__)

@terminal_bp.route('/')
def index():
    return "<h1>Terminal</h1>"

@socketio.on('run_command')
def handle_command(data):
    cmd = data.get('command')
    if not cmd: return
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            socketio.emit('cmd_output', {'output': line.rstrip()})
        proc.wait()
        socketio.emit('cmd_output', {'output': f'Command finished with code {proc.returncode}', 'exit': proc.returncode})
    except Exception as e:
        socketio.emit('cmd_output', {'output': f'Error: {e}', 'exit': -1})
