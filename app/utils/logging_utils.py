import logging
from datetime import datetime
import os

def setup_logger():
    # Log directory
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Log format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler for general logs
    file_handler = logging.FileHandler(f'logs/app.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Setup main logger
    logger = logging.getLogger('VPScope')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_user_action(user, action, details=None):
    logger = logging.getLogger('VPScope')
    if not logger.handlers:
        setup_logger()
    logger.info(f"User '{user}' performed action: {action} | Details: {details}")

def log_system_event(event, details=None):
    logger = logging.getLogger('VPScope')
    if not logger.handlers:
        setup_logger()
    logger.info(f"System event: {event} | Details: {details}")
