from flask import Blueprint, jsonify
from app.utils.system_utils import get_summary_metrics

system_bp = Blueprint('system', __name__)

@system_bp.route('/')
def index():
    return "<h1>System Metrics API</h1>"

@system_bp.route('/metrics')
def metrics():
    metrics_data = get_summary_metrics()
    return jsonify(metrics_data)
