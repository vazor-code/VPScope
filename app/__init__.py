from flask import Flask, redirect, url_for
from flask_socketio import SocketIO
from flask_login import LoginManager
from datetime import timedelta
import os
from app.utils.logging_utils import setup_logger

# Global SocketIO
socketio = SocketIO(async_mode='threading')

# Login manager
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="static")
    app.config['SECRET_KEY'] = os.urandom(24).hex()
    app.config['LOGIN_VIEW'] = 'index.login'  # Important!
    app.config['LOGIN_MESSAGE'] = "Please log in to access this page."
    app.config['LOGIN_MESSAGE_CATEGORY'] = 'info'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)

    # Initialize LoginManager
    login_manager.init_app(app)

    # Register blueprints
    from app.routes.index import index_bp
    from app.routes.system import system_bp
    from app.routes.files import files_bp
    from app.routes.terminal import terminal_bp

    app.register_blueprint(index_bp)
    app.register_blueprint(system_bp, url_prefix='/system')
    app.register_blueprint(files_bp, url_prefix='/files')
    app.register_blueprint(terminal_bp, url_prefix='/terminal')

    @app.errorhandler(401)
    def unauthorized(e):
        return redirect(url_for('index.login'))

    return app

def run_server(host='0.0.0.0', port=8000):
    import sys

    # Setup logging
    logger = setup_logger()

    app = create_app()
    socketio.init_app(app)

    logger.info(f"Starting VPScope server on {host}:{port}")
    try:
        socketio.run(app, host=host, port=port, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Shutting down VPScope immediately...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        sys.exit(1)
