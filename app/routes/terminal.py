from flask import Blueprint
from app import socketio
from app.utils.terminal_utils import run_command

terminal_bp = Blueprint('terminal', __name__)

@terminal_bp.route('/')
def index():
    return "<h1>Terminal API</h1>"

@socketio.on('run_command')
def handle_command(data):
    cmd = data.get('command')
    if not cmd:
        socketio.emit('cmd_output', {'output': 'No command provided.', 'exit': -1})
        return
    run_command(cmd, socketio.emit)
