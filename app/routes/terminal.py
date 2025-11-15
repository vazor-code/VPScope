from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import socketio
from app.utils.terminal_utils import run_command

terminal_bp = Blueprint('terminal', __name__)

@terminal_bp.route('/')
@login_required
def index():
    return render_template('terminal.html')

@socketio.on('run_command', namespace='/terminal')
def handle_command(data):
    if not current_user.is_authenticated:
        socketio.emit('cmd_output', {'output': 'Not authenticated.'}, namespace='/terminal')
        return
    cmd = data.get('command')
    if not cmd:
        socketio.emit('cmd_output', {'output': 'No command provided.', 'exit': -1}, namespace='/terminal')
        return
    run_command(cmd, lambda event, data: socketio.emit(event, data, namespace='/terminal'))
