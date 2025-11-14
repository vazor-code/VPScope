from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO(async_mode='eventlet')

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config['SECRET_KEY'] = 'change-me'

    from .routes.system import system_bp
    from .routes.files import files_bp
    from .routes.terminal import terminal_bp

    app.register_blueprint(system_bp, url_prefix='/system')
    app.register_blueprint(files_bp, url_prefix='/files')
    app.register_blueprint(terminal_bp, url_prefix='/terminal')

    socketio.init_app(app)
    return app
