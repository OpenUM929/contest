"""
트레이트 수정 라우트 (페이지 + API)
"""
from flask import Blueprint, request, jsonify, render_template
from pathlib import Path
import json

# 페이지 라우트
page_bp = Blueprint('edit_traits_page', __name__, url_prefix='/edit')

@page_bp.route('/traits')
def edit_traits_page():
    """트레이트 수정 페이지"""
    return render_template('edit_traits.html')

# API 라우트
api_bp = Blueprint('edit_traits_api', __name__, url_prefix='/api/edit')

PROJECT = Path(__file__).parent.parent.parent

def get_trait_folder(trait_id):
    """trait_id에 따라 폴더 결정"""
    if trait_id.startswith('T1') and len(trait_id) == 3:
        return 'positive'
    return 'negative'

@api_bp.route('/traits', methods=['GET'])
def list_traits():
    """전체 트레이트 조회"""
    traits = {'positive': [], 'negative': []}
    
    for ttype in ['positive', 'negative']:
        src_dir = PROJECT / 'data' / 'traits' / ttype
        if not src_dir.exists():
            continue
        
        for json_file in sorted(src_dir.glob('*.json')):
            with open(json_file, 'r', encoding='utf-8') as f:
                trait = json.load(f)
                traits[ttype].append(trait)
    
    return jsonify({
        'positive': traits['positive'],
        'negative': traits['negative'],
        'total': len(traits['positive']) + len(traits['negative'])
    })

@api_bp.route('/traits/<trait_id>', methods=['GET'])
def get_trait(trait_id):
    """개별 트레이트 조회"""
    folder = get_trait_folder(trait_id)
    file_path = PROJECT / 'data' / 'traits' / folder / f'{trait_id}.json'
    
    if not file_path.exists():
        return jsonify({'error': 'Trait not found'}), 404
    
    with open(file_path, 'r', encoding='utf-8') as f:
        trait = json.load(f)
    
    return jsonify(trait)

@api_bp.route('/traits/<trait_id>', methods=['PUT'])
def update_trait(trait_id):
    """트레이트 수정"""
    from src.data_validator import validate_and_save_trait
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success, result = validate_and_save_trait(data)
    
    if not success:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    return jsonify({'message': 'Trait updated successfully', 'trait_id': trait_id})

@api_bp.route('/traits', methods=['POST'])
def create_trait():
    """새 트레이트 추가"""
    from src.data_validator import validate_and_save_trait
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    trait_id = data.get('trait_id')
    if not trait_id:
        return jsonify({'error': 'trait_id required'}), 400
    
    folder = get_trait_folder(trait_id)
    file_path = PROJECT / 'data' / 'traits' / folder / f'{trait_id}.json'
    
    if file_path.exists():
        return jsonify({'error': 'Trait already exists'}), 409
    
    success, result = validate_and_save_trait(data)
    
    if not success:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    return jsonify({'message': 'Trait created successfully', 'trait_id': trait_id})

@api_bp.route('/traits/<trait_id>', methods=['DELETE'])
def delete_trait(trait_id):
    """트레이트 삭제"""
    from src.backup_manager import create_backup
    
    folder = get_trait_folder(trait_id)
    file_path = PROJECT / 'data' / 'traits' / folder / f'{trait_id}.json'
    
    if not file_path.exists():
        return jsonify({'error': 'Trait not found'}), 404
    
    create_backup(file_path)
    file_path.unlink()
    
    return jsonify({'message': 'Trait deleted successfully'})

@api_bp.route('/traits/integrate', methods=['POST'])
def integrate_traits():
    """트레이트 통합 파일 갱신"""
    from src.data_integrator import integrate_traits
    
    try:
        result_path = integrate_traits()
        return jsonify({
            'message': 'Traits integrated',
            'file': result_path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
