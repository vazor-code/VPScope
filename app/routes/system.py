from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from app.utils.system_utils import get_summary_metrics
from app import cache

system_bp = Blueprint('system', __name__)

@system_bp.route('/')
@login_required
def index():
    return render_template('system.html')

@system_bp.route('/metrics')
@login_required
@cache.cached(timeout=5, key_prefix='system_metrics')
def metrics():
    metrics_data = get_summary_metrics()
    return jsonify(metrics_data)
