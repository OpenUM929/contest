"""Metadata routes"""
from flask import Blueprint, request, jsonify, session
from src.metadata import (
    get_user_metadata, get_all_users_summary,
    get_user_history, calculate_trait_delta, calculate_trait_trend,
    analyze_cohort, analyze_gap, generate_insights, generate_cohort_insights
)

metadata_bp = Blueprint('metadata', __name__)

@metadata_bp.route('/api/metadata/users', methods=['GET'])
def get_metadata_users():
    filter_department = request.args.get('department')
    filter_position = request.args.get('position')
    filter_job_level = request.args.get('job_level')
    
    users_summary = get_all_users_summary()
    users = users_summary.get('users', [])
    
    if filter_department:
        users = [u for u in users if u.get('department') == filter_department]
    if filter_position:
        users = [u for u in users if u.get('position') == filter_position]
    if filter_job_level:
        users = [u for u in users if u.get('job_level') == filter_job_level]
    
    return jsonify({
        'total': len(users),
        'users': users
    })

@metadata_bp.route('/api/metadata/user/<user_key>', methods=['GET'])
def get_metadata_user(user_key):
    user = get_user_metadata(user_key)
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
    
    return jsonify(user)

@metadata_bp.route('/api/metadata/user/<user_key>/history', methods=['GET'])
def get_metadata_user_history(user_key):
    history = get_user_history(user_key)
    deltas = calculate_trait_delta(user_key)
    trends = calculate_trait_trend(user_key)
    insights = generate_insights(user_key)
    
    return jsonify({
        'history': history,
        'trait_delta': deltas,
        'trait_trend': trends,
        'insights': insights
    })

@metadata_bp.route('/api/metadata/cohort', methods=['GET'])
def get_cohort_analysis():
    cohort_type = request.args.get('type', 'department')
    cohort_value = request.args.get('value', '')
    
    if not cohort_value:
        return jsonify({'error': 'cohort_value를 지정해주세요.'}), 400
    
    cohort = analyze_cohort(cohort_type, cohort_value)
    gap = analyze_gap(cohort_type, cohort_value)
    insights = generate_cohort_insights(cohort_type, cohort_value)
    
    return jsonify({
        'cohort': cohort,
        'gap_analysis': gap,
        'insights': insights
    })

@metadata_bp.route('/api/metadata/insights/user/<user_key>', methods=['GET'])
def get_user_insights(user_key):
    insights = generate_insights(user_key)
    return jsonify({'insights': insights})

@metadata_bp.route('/api/metadata/insights/cohort', methods=['GET'])
def get_cohort_insights():
    cohort_type = request.args.get('type', 'department')
    cohort_value = request.args.get('value', '')
    
    if not cohort_value:
        return jsonify({'error': 'cohort_value를 지정해주세요.'}), 400
    
    insights = generate_cohort_insights(cohort_type, cohort_value)
    return jsonify({'insights': insights})