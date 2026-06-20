"""Dashboard routes"""
from flask import Blueprint, render_template, request, jsonify, session
from src.auth import get_dashboard_summary, get_dashboard_by_period, get_recent_analyses
from src.config import get_trait_name_map

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    username = session.get('username', 'Guest')
    return render_template('dashboard.html', user_id=user_id, username=username)

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    period = request.args.get('period', 'all')
    filter_department = request.args.get('department', '')
    filter_position = request.args.get('position', '')
    filter_job_level = request.args.get('job_level', '')
    
    summary = get_dashboard_summary()
    period_data = get_dashboard_by_period(period, filter_department, filter_position, filter_job_level)
    recent = get_recent_analyses(10, filter_department, filter_position, filter_job_level)
    
    trait_name_map = get_trait_name_map()
    
    for item in period_data['trait_distribution']:
        item['name'] = trait_name_map.get(item['trait_id'], 'Unknown')
    for item in period_data['trait_percentages']:
        item['name'] = trait_name_map.get(item['trait_id'], 'Unknown')
    for item in recent:
        item['primary_name'] = trait_name_map.get(item['primary_trait'], '-')
    
    return jsonify({
        'summary': summary,
        'data': period_data,
        'recent_analyses': recent
    })