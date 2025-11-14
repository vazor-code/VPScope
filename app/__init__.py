from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager

# Глобальный SocketIO
socketio = SocketIO(async_mode='threading')

# Логин менеджер
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="static")
    app.config['SECRET_KEY'] = 'your-super-secret-key-change-this'
    app.config['LOGIN_VIEW'] = 'index.login'  # ← Это важно!
    app.config['LOGIN_MESSAGE'] = "Please log in to access this page."
    app.config['LOGIN_MESSAGE_CATEGORY'] = 'info'

    # Инициализация LoginManager
    login_manager.init_app(app)
    login_manager.login_message = "Please log in to access this page."

    # Регистрация blueprints
    from app.routes.index import index_bp
    from app.routes.system import system_bp
    from app.routes.files import files_bp
    from app.routes.terminal import terminal_bp

    app.register_blueprint(index_bp)
    app.register_blueprint(system_bp, url_prefix='/system')
    app.register_blueprint(files_bp, url_prefix='/files')
    app.register_blueprint(terminal_bp, url_prefix='/terminal')

    return app

def run_server(host='0.0.0.0', port=8000):
    import logging, sys

    # Логирование
    logger = logging.getLogger('VPScope')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        class ColorFormatter(logging.Formatter):
            COLORS = {
                'INFO': '\033[92m',
                'WARNING': '\033[93m',
                'ERROR': '\033[91m',
                'DEBUG': '\033[96m',
            }
            RESET = '\033[0m'
            def format(self, record):
                color = self.COLORS.get(record.levelname, self.RESET)
                msg = super().format(record)
                return f"{color}{msg}{self.RESET}"
        ch = logging.StreamHandler()
        ch.setFormatter(ColorFormatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S'))
        logger.addHandler(ch)

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
