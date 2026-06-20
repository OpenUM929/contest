"""Authentication routes"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from src.auth import create_user, verify_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login_page():
    if session.get('user_id'):
        return redirect(url_for('index'))
    return render_template('login.html')

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '아이디와 비밀번호를 입력해주세요.'}), 400
    
    result = create_user(username, password)
    return jsonify(result)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    result = verify_user(username, password)
    
    if result['success']:
        session['user_id'] = result['user_id']
        session['username'] = result['username']
    
    return jsonify(result)

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/api/auth/check', methods=['GET'])
def check_auth():
    user_id = session.get('user_id')
    username = session.get('username')
    
    if user_id:
        return jsonify({
            'authenticated': True,
            'user_id': user_id,
            'username': username
        })
    return jsonify({'authenticated': False})