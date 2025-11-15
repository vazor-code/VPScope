from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import login_manager
from app.utils.logging_utils import log_user_action

index_bp = Blueprint('index', __name__)

# Simple user database (use DB in real project)
USERS = {
    'admin': {'password': generate_password_hash('admin123'), 'id': 1}  # Hash password
}

class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    for username, data in USERS.items():
        if str(data['id']) == user_id:
            return User(data['id'], username)
    return None

@index_bp.route('/')
@login_required
def index():
    log_user_action(current_user.username, 'Accessed dashboard')
    return render_template('index.html')

@index_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me') == 'on'
        user_data = USERS.get(username)
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['id'], username)
            login_user(user, remember=remember)
            log_user_action(username, 'Login successful')
            return redirect(url_for('index.index'))
        else:
            flash('Invalid credentials', 'error')
            log_user_action(username or 'Unknown', 'Login failed')
    return render_template('login.html')

@index_bp.route('/logout')
@login_required
def logout():
    log_user_action(current_user.username, 'Logout')
    logout_user()
    return redirect(url_for('index.login'))
