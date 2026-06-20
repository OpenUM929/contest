"""Analysis routes"""
from flask import Blueprint, render_template, request, jsonify, session
from src.nlp_pipeline import (
    build_llm_prompt, validate_structure,
    apply_calibration, filter_low_confidence,
    apply_sentence_weights, create_opencode_client, call_llm_with_retry
)
from src.config import (
    get_label_config, get_grouped_labels, get_calibration_map, 
    get_conflict_axis_map, get_engine, get_trait_name_map,
    get_trait_details, get_label_details, get_macro_category
)
from src.auth import save_analysis_result
from src.metadata import save_analysis_metadata

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/')
def index():
    allowed_labels, label_name_map = get_label_config()
    trait_map = get_trait_name_map()
    user_id = session.get('user_id')
    username = session.get('username', 'Guest')
    return render_template(
        'index.html',
        label_count=len(allowed_labels),
        labels_preview=list(label_name_map.items())[:10],
        trait_map=trait_map,
        user_id=user_id,
        username=username
    )

@analysis_bp.route('/bulk')
def bulk_analysis():
    user_id = session.get('user_id')
    username = session.get('username', 'Guest')
    return render_template('bulk.html', user_id=user_id, username=username)

@analysis_bp.route('/api/generate-prompt', methods=['POST'])
def generate_prompt():
    data = request.get_json()
    user_input = data.get('text', '')
    
    if not user_input:
        return jsonify({'error': '텍스트를 입력해주세요.'}), 400
    
    allowed_labels, label_name_map = get_label_config()
    prompt = build_llm_prompt(user_input, allowed_labels, label_name_map)
    
    return jsonify({
        'prompt': prompt,
        'prompt_length': len(prompt)
    })

@analysis_bp.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    user_input = data.get('text', '')
    llm_response = data.get('llm_response', '')
    mode = data.get('mode', 'auto')
    llm_provider = data.get('llm_provider', 'gemini')
    
    debug_info = []
    
    if not user_input:
        return jsonify({'error': '텍스트를 입력해주세요.'}), 400
    
    allowed_labels, label_name_map = get_label_config()
    grouped_labels = get_grouped_labels()
    calibration_map = get_calibration_map()
    conflict_axis_map = get_conflict_axis_map()
    
    # Step 1: 프롬프트 생성
    prompt = build_llm_prompt(user_input, allowed_labels, label_name_map, grouped_labels)
    debug_info.append({
        'step': 1,
        'name': '프롬프트 생성',
        'input': user_input[:100] + '...' if len(user_input) > 100 else user_input,
        'output': prompt[:500] + '...' if len(prompt) > 500 else prompt,
        'details': f'프롬프트 길이: {len(prompt)}자'
    })
    
    # Step 2: LLM 응답 획득
    if mode == 'auto':
        try:
            llm = create_opencode_client()
            raw_response = call_llm_with_retry(llm, prompt, allowed_labels)
            llm_response = __import__('json').dumps(raw_response, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = str(e)
            if 'opencode' in error_msg.lower():
                user_message = f"OpenCode API 오류: {error_msg}"
            else:
                user_message = f"분석 중 오류 발생: {error_msg}"
            return jsonify({'error': user_message}), 500
    else:
        try:
            raw_response = __import__('json').loads(llm_response)
        except __import__('json').JSONDecodeError:
            return jsonify({'error': 'LLM 응답이 유효한 JSON 형식이 아닙니다.'}), 400
        
        is_valid, error_msg = validate_structure(raw_response, allowed_labels)
        if not is_valid:
            return jsonify({'error': f'구조 검증 실패: {error_msg}'}), 400
    
    debug_info.append({
        'step': 2,
        'name': 'LLM 응답',
        'input': prompt[:200] + '...',
        'output': llm_response[:500] + '...' if len(llm_response) > 500 else llm_response,
        'details': 'JSON 파싱 성공'
    })
    
    # Step 3: Calibration
    extracted = __import__('json').loads(llm_response) if isinstance(llm_response, str) else llm_response
    before_cal = [[l['label_id'], l['confidence']] for s in extracted['sentences'] for l in s['labels']]
    extracted = apply_calibration(extracted, calibration_map)
    after_cal = [[l['label_id'], l['confidence']] for s in extracted['sentences'] for l in s['labels']]
    
    debug_info.append({
        'step': 3,
        'name': 'Calibration',
        'input': str(before_cal[:5]),
        'output': str(after_cal[:5]),
        'details': f'보정 계수: 0.88'
    })
    
    # Step 4: Low Confidence 필터링
    before_filter = sum(len(s['labels']) for s in extracted['sentences'])
    extracted = filter_low_confidence(extracted, threshold=0.5)
    after_filter = sum(len(s['labels']) for s in extracted['sentences'])
    
    debug_info.append({
        'step': 4,
        'name': '필터링 (threshold=0.5)',
        'input': f'전체 {before_filter}개',
        'output': f'필터링 후 {after_filter}개',
        'details': f'제거된 라벨: {before_filter - after_filter}개'
    })
    
    # Step 5: 문장 Weight 적용
    extracted = apply_sentence_weights(extracted)
    weights = {s['text'][:30]: s.get('sentence_weight', 1.0) for s in extracted['sentences']}
    
    debug_info.append({
        'step': 5,
        'name': '문장 Weight',
        'input': '문장 중요도 키워드',
        'output': str(weights),
        'details': 'IMPORTANCE_KEYWORD 포함 시 1.2'
    })
    
    # Step 6: Trait 추론
    micro_labels_for_engine = [
        {
            'label_id': l['label_id'],
            'label_name': l.get('reason', 'N/A'),
            'macro_category': get_macro_category(l['label_id']),
            'confidence': l['confidence']
        }
        for s in extracted['sentences']
        for l in s['labels']
    ]
    
    engine = get_engine()
    trait_result = engine.process(micro_labels_for_engine)
    trait_name_map = get_trait_name_map()
    
    debug_info.append({
        'step': 6,
        'name': 'Trait 추론',
        'input': str([l['label_id'] for l in micro_labels_for_engine[:5]]) + '...',
        'output': f"Primary: {trait_result.get('primary')}, Positive: {len([t for t in trait_result.get('sorted_trait_list', [])])}, Negative: {len(trait_result.get('negative_traits', []))}",
        'details': f"Secondary: {trait_result.get('secondary')}, sorted: {trait_result.get('sorted_trait_list', [])}"
    })
    
    primary_trait_id = trait_result['primary']
    primary_trait_type = trait_result.get('primary_type', 'positive')
    primary_trait_details = get_trait_details(primary_trait_id)
    
    secondary_traits_details = [get_trait_details(t) for t in trait_result['secondary']]
    
    top_labels = sorted(micro_labels_for_engine, key=lambda x: x['confidence'], reverse=True)[:5]
    label_details = []
    for l in top_labels:
        details = get_label_details(l['label_id'])
        label_details.append({
            'label_id': l['label_id'],
            'name': details['name'],
            'definition': details['definition'],
            'confidence': l['confidence'],
            'macro_category': l['macro_category']
        })
    
    sorted_trait_list = trait_result.get('sorted_trait_list', [])
    negative_traits = trait_result.get('negative_traits', [])
    
    trait_percentage_with_names = [
        {
            'trait_id': t[0],
            'name': trait_name_map.get(t[0], 'Unknown'),
            'percentage': t[1],
            'type': t[3] if len(t) > 3 else 'positive'
        }
        for t in sorted_trait_list
    ]
    
    negative_traits_with_names = [
        {
            'trait_id': n['trait_id'],
            'name': trait_name_map.get(n['trait_id'], 'Unknown'),
            'severity': n['severity']
        }
        for n in negative_traits
    ]
    
    result = {
        'success': True,
        'input_text': user_input,
        'mode': mode,
        'llm_response': llm_response,
        'extracted_labels': extracted,
        'trait_result': {
            'primary': primary_trait_id,
            'primary_type': primary_trait_type,
            'primary_name': primary_trait_details['name'] if primary_trait_details else 'Unknown',
            'primary_description': primary_trait_details.get('description', '') if primary_trait_details else '',
            'strengths': primary_trait_details.get('strengths', []) if primary_trait_details else [],
            'risks': primary_trait_details.get('risks', []) if primary_trait_details else [],
            'secondary': trait_result['secondary'],
            'secondary_details': [
                {
                    'trait_id': t,
                    'name': d['name'] if d else 'Unknown',
                    'description': d.get('description', '') if d else '',
                    'type': t[3] if len(t) > 3 else 'positive'
                }
                for t, d in zip(trait_result['secondary'], secondary_traits_details)
            ],
            'confidence': trait_result['confidence'],
            'evidence': trait_result['evidence'],
            'trait_percentages': trait_percentage_with_names,
            'negative_traits': negative_traits_with_names
        },
        'important_labels': label_details,
        'debug_info': debug_info
    }
    
    # 분석 결과 저장
    user_id = session.get('user_id')
    user_key = session.get('username')
    if user_id:
        try:
            result_json = __import__('json').dumps(result, ensure_ascii=False)
            trait_result_str = __import__('json').dumps(trait_result, ensure_ascii=False)
            save_analysis_result(user_id, user_input, result_json, trait_result_str)
            
            if user_key:
                save_analysis_metadata(user_key, result)
        except Exception as e:
            print(f"결과 저장 실패: {e}")
    
    return jsonify(result)

@analysis_bp.route('/api/labels', methods=['GET'])
def get_all_labels():
    allowed_labels, label_name_map = get_label_config()
    labels = [{'id': k, 'name': v} for k, v in label_name_map.items()]
    return jsonify({'labels': labels})

@analysis_bp.route('/api/traits', methods=['GET'])
def get_all_traits():
    trait_map = get_trait_name_map()
    traits = [{'id': k, 'name': v} for k, v in trait_map.items()]
    return jsonify({'traits': traits})