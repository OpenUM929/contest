"""
라벨 수정 라우트 (페이지 + API)
"""
from flask import Blueprint, request, jsonify, send_file, render_template
from pathlib import Path
import json

# 페이지 라우트
page_bp = Blueprint('edit_labels_page', __name__, url_prefix='/edit')

@page_bp.route('/labels')
def edit_labels_page():
    """라벨 수정 페이지"""
    return render_template('edit_labels.html')

# API 라우트
api_bp = Blueprint('edit_labels_api', __name__, url_prefix='/api/edit')

PROJECT = Path(__file__).parent.parent.parent

@api_bp.route('/labels/<label_type>', methods=['GET'])
def list_labels(label_type):
    """개별 라벨 파일 목록 조회"""
    if label_type not in ['positive', 'negative']:
        return jsonify({'error': 'Invalid type'}), 400
    
    src_dir = PROJECT / 'data' / 'micro_labels' / label_type
    if not src_dir.exists():
        return jsonify({'labels': [], 'count': 0})
    
    labels = []
    for json_file in sorted(src_dir.glob('*.json')):
        with open(json_file, 'r', encoding='utf-8') as f:
            label = json.load(f)
            labels.append(label)
    
    return jsonify({'labels': labels, 'count': len(labels)})

@api_bp.route('/labels/<label_type>/<label_id>', methods=['GET'])
def get_label(label_type, label_id):
    """개별 라벨 조회"""
    file_path = PROJECT / 'data' / 'micro_labels' / label_type / f'{label_id}.json'
    
    if not file_path.exists():
        return jsonify({'error': 'Label not found'}), 404
    
    with open(file_path, 'r', encoding='utf-8') as f:
        label = json.load(f)
    
    return jsonify(label)

@api_bp.route('/labels/<label_type>/<label_id>', methods=['PUT'])
def update_label(label_type, label_id):
    """라벨 수정"""
    from src.data_validator import validate_and_save_label
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success, result = validate_and_save_label(data, label_type, label_id)
    
    if not success:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    return jsonify({'message': 'Label updated successfully', 'label_id': label_id})

@api_bp.route('/labels/<label_type>', methods=['POST'])
def create_label(label_type):
    """새 라벨 추가"""
    from src.data_validator import validate_and_save_label
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    label_id = data.get('label_id')
    if not label_id:
        return jsonify({'error': 'label_id required'}), 400
    
    file_path = PROJECT / 'data' / 'micro_labels' / label_type / f'{label_id}.json'
    if file_path.exists():
        return jsonify({'error': 'Label already exists'}), 409
    
    success, result = validate_and_save_label(data, label_type, label_id)
    
    if not success:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    return jsonify({'message': 'Label created successfully', 'label_id': label_id})

@api_bp.route('/labels/<label_type>/<label_id>', methods=['DELETE'])
def delete_label(label_type, label_id):
    """라벨 삭제"""
    from src.backup_manager import create_backup
    
    file_path = PROJECT / 'data' / 'micro_labels' / label_type / f'{label_id}.json'
    
    if not file_path.exists():
        return jsonify({'error': 'Label not found'}), 404
    
    create_backup(file_path)
    file_path.unlink()
    
    return jsonify({'message': 'Label deleted successfully'})

@api_bp.route('/integrate', methods=['POST'])
def integrate_data():
    """AI 검토용 통합 파일 생성"""
    from src.data_integrator import full_integrate
    
    try:
        result_path = full_integrate()
        return jsonify({
            'message': 'Integration complete',
            'file': result_path,
            'download_url': '/api/edit/download_integrated'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/download_integrated', methods=['GET'])
def download_integrated():
    """통합 파일 다운로드"""
    file_path = PROJECT / 'temp' / 'integrated_data.json'
    
    if not file_path.exists():
        return jsonify({'error': 'Integrated file not found. Run integration first.'}), 404
    
    return send_file(file_path, mimetype='application/json', as_attachment=True)
