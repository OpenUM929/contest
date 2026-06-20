"""
Flask Web Application for Leadership Analysis System
리더십 분석 시스템 웹 인터페이스
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from src.nlp_pipeline import (
    load_allowed_labels,
    build_llm_prompt,
    validate_structure,
    apply_calibration,
    filter_low_confidence,
    apply_sentence_weights,
    detect_conflicts,
    create_opencode_client,
    call_llm_with_retry,
    run_extraction_pipeline
)
from src.vector_search import VectorSearcher
from src.leadership_engine import LeadershipEngine
from src.auth import (
    create_user, verify_user, get_user_by_id,
    save_analysis_result, get_user_analysis_results,
    get_dashboard_stats, get_trait_distribution, get_positive_negative_ratio,
    get_trait_percentages, get_category_distribution, get_daily_trend, get_recent_analyses,
    get_negative_trait_count, get_top_trait, get_dashboard_summary, get_dashboard_by_period
)
from src.database import init_db
from src.metadata import (
    save_analysis_metadata, get_user_metadata, get_user_profile,
    get_user_results, get_user_history, calculate_trait_delta, get_all_users_summary,
    calculate_trait_trend, analyze_cohort, analyze_gap, generate_insights, generate_cohort_insights
)
from src.routes.edit_labels import page_bp as edit_labels_page_bp, api_bp as edit_labels_api_bp
from src.routes.edit_traits import page_bp as edit_traits_page_bp, api_bp as edit_traits_api_bp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize database
init_db()

# Register edit blueprints (page + api)
app.register_blueprint(edit_labels_page_bp)
app.register_blueprint(edit_labels_api_bp)
app.register_blueprint(edit_traits_page_bp)
app.register_blueprint(edit_traits_api_bp)

# Global instances
_engine = None
_allowed_labels = None
_label_name_map = None
_conflict_axis_map = {}
_macro_category_map = None
_vector_searcher = None

def get_vector_searcher():
    global _vector_searcher
    if _vector_searcher is None:
        _vector_searcher = VectorSearcher()
    return _vector_searcher

def get_engine():
    global _engine
    if _engine is None:
        _engine = LeadershipEngine(data_dir='./data')
    return _engine

def get_label_config():
    global _allowed_labels, _label_name_map
    if _allowed_labels is None:
        # Micro Labels에서 ID → (이름, 정의) 매핑 로드
        _label_name_map = {}
        for fname in ['data/micro_labels/positive_micro_labels.json', 
                      'data/micro_labels/negative_micro_labels.json']:
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for ml in data.get('micro_labels', []):
                        label_id = ml['label_id']
                        label_name = ml.get('label_name', '')
                        definition = ml.get('definition', '')
                        if definition:
                            _label_name_map[label_id] = f"{label_name}: {definition}"
                        else:
                            _label_name_map[label_id] = label_name
            except FileNotFoundError:
                pass
        
        # Labels 스키마에서 allowed set 로드
        with open('data/labels/positive_labels.json', 'r', encoding='utf-8') as f:
            label_schema = json.load(f)
        _allowed_labels, _ = load_allowed_labels(label_schema)
        
        # Negative labels도 추가
        try:
            with open('data/labels/negative_labels.json', 'r', encoding='utf-8') as f:
                neg_schema = json.load(f)
            neg_allowed, _ = load_allowed_labels(neg_schema)
            _allowed_labels.update(neg_allowed)
        except FileNotFoundError:
            pass
            
    return _allowed_labels, _label_name_map

def get_conflict_axis_map():
    global _conflict_axis_map
    if not _conflict_axis_map:
        _conflict_axis_map = {
            "M33-01": "integrity", "M33-03": "integrity", "M30-01": "integrity",
            "N30-01": "integrity", "N28-01": "transparency"
        }
    return _conflict_axis_map

def get_macro_category_map():
    """JSON에서 Micro Label → Macro Category 매핑 동적 로드"""
    global _macro_category_map
    if _macro_category_map is None:
        _macro_category_map = {}
        for fname in ['data/labels/positive_labels.json', 'data/labels/negative_labels.json']:
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for label in data.get('labels', []):
                        category = label.get('category', '기타')
                        for micro_id in label.get('micro_labels', []):
                            _macro_category_map[micro_id] = category
            except FileNotFoundError:
                pass
    return _macro_category_map

def get_grouped_labels():
    """카테고리별 그룹화된 라벨 목록 반환"""
    grouped = {}
    for fname in ['data/labels/positive_labels.json', 'data/labels/negative_labels.json']:
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for label in data.get('labels', []):
                    category = label.get('category', '기타')
                    micro_ids = label.get('micro_labels', [])
                    if category not in grouped:
                        grouped[category] = []
                    grouped[category].extend(micro_ids)
        except FileNotFoundError:
            pass
    return grouped

def get_macro_category(label_id: str) -> str:
    """Micro Label ID → Macro Category 매핑"""
    macro_map = get_macro_category_map()
    return macro_map.get(label_id, "기타")

def get_trait_name_map():
    with open('data/traits/trait_definitions.json', 'r', encoding='utf-8') as f:
        trait_data = json.load(f)
    return {t['trait_id']: t['trait_name'] for t in trait_data['traits']}

def get_trait_details(trait_id):
    if not trait_id:
        return None
    with open('data/traits/trait_definitions.json', 'r', encoding='utf-8') as f:
        trait_data = json.load(f)
    for t in trait_data['traits']:
        if t['trait_id'] == trait_id:
            return {
                'name': t['trait_name'],
                'description': t.get('description', ''),
                'strengths': t.get('strengths', []),
                'risks': t.get('risks', [])
            }
    return None

def get_label_details(label_id):
    with open('data/micro_labels/positive_micro_labels.json', 'r', encoding='utf-8') as f:
        label_data = json.load(f)
    for ml in label_data.get('micro_labels', []):
        if ml['label_id'] == label_id:
            return {
                'name': ml['label_name'],
                'definition': ml.get('definition', '')
            }
    with open('data/micro_labels/negative_micro_labels.json', 'r', encoding='utf-8') as f:
        label_data = json.load(f)
    for ml in label_data.get('micro_labels', []):
        if ml['label_id'] == label_id:
            return {
                'name': ml['label_name'],
                'definition': ml.get('definition', '')
            }
    return {'name': 'Unknown', 'definition': ''}

def get_calibration_map():
    return {"default": 0.88}

@app.route('/')
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

@app.route('/login')
def login_page():
    """로그인 페이지"""
    if session.get('user_id'):
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/auth/register', methods=['POST'])
def register():
    """회원가입"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '아이디와 비밀번호를 입력해주세요.'}), 400
    
    result = create_user(username, password)
    return jsonify(result)

@app.route('/api/auth/login', methods=['POST'])
def login():
    """로그인"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    result = verify_user(username, password)
    
    if result['success']:
        session['user_id'] = result['user_id']
        session['username'] = result['username']
    
    return jsonify(result)

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """로그아웃"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """인증 상태 확인"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    if user_id:
        return jsonify({
            'authenticated': True,
            'user_id': user_id,
            'username': username
        })
    return jsonify({'authenticated': False})

@app.route('/dashboard')
def dashboard():
    """대시보드 페이지"""
    user_id = session.get('user_id')
    username = session.get('username', 'Guest')
    return render_template('dashboard.html', user_id=user_id, username=username)

@app.route('/bulk')
def bulk_analysis():
    """대규모 분석 페이지"""
    user_id = session.get('user_id')
    username = session.get('username', 'Guest')
    return render_template('bulk.html', user_id=user_id, username=username)

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """대시보드 통계 데이터"""
    period = request.args.get('period', 'all')
    filter_department = request.args.get('department', '')
    filter_position = request.args.get('position', '')
    filter_job_level = request.args.get('job_level', '')
    
    summary = get_dashboard_summary()
    period_data = get_dashboard_by_period(period, filter_department, filter_position, filter_job_level)
    recent = get_recent_analyses(10, filter_department, filter_position, filter_job_level)
    
    trait_name_map = get_trait_name_map()
    
    # Trait 이름 매핑
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

@app.route('/api/metadata/users', methods=['GET'])
def get_metadata_users():
    """메타데이터 기반 사용자 목록 (집단 분석용)"""
    filter_department = request.args.get('department')
    filter_position = request.args.get('position')
    filter_job_level = request.args.get('job_level')
    
    users_summary = get_all_users_summary()
    users = users_summary.get('users', [])
    
    # 필터 적용
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

@app.route('/api/metadata/user/<user_key>', methods=['GET'])
def get_metadata_user(user_key):
    """특정 사용자 메타데이터 조회"""
    user = get_user_metadata(user_key)
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
    
    return jsonify(user)

@app.route('/api/metadata/user/<user_key>/history', methods=['GET'])
def get_metadata_user_history(user_key):
    """사용자 이력 및 Delta 조회 - Phase 2"""
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

@app.route('/api/metadata/cohort', methods=['GET'])
def get_cohort_analysis():
    """집단 분석 - Phase 3"""
    cohort_type = request.args.get('type', 'department')
    cohort_value = request.args.get('value', '')
    
    if not cohort_value:
        return jsonify({'error': ' cohort_value를 지정해주세요.'}), 400
    
    cohort = analyze_cohort(cohort_type, cohort_value)
    gap = analyze_gap(cohort_type, cohort_value)
    insights = generate_cohort_insights(cohort_type, cohort_value)
    
    return jsonify({
        'cohort': cohort,
        'gap_analysis': gap,
        'insights': insights
    })

@app.route('/api/metadata/insights/user/<user_key>', methods=['GET'])
def get_user_insights(user_key):
    """사용자 인사이트 - Phase 4"""
    insights = generate_insights(user_key)
    return jsonify({'insights': insights})

@app.route('/api/metadata/insights/cohort', methods=['GET'])
def get_cohort_insights():
    """집단 인사이트 - Phase 4"""
    cohort_type = request.args.get('type', 'department')
    cohort_value = request.args.get('value', '')
    
    if not cohort_value:
        return jsonify({'error': ' cohort_value를 지정해주세요.'}), 400
    
    insights = generate_cohort_insights(cohort_type, cohort_value)
    return jsonify({'insights': insights})

@app.route('/api/generate-prompt', methods=['POST'])
def generate_prompt():
    """프롬프트 생성만 수행"""
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

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """표준 분석 파이프라인: Vector DB → 임계값 판단 → LLM(필요시) → Trait 추론"""
    data = request.get_json()
    user_input = data.get('text', '').strip()
    mode = data.get('mode', 'auto')
    
    if not user_input:
        return jsonify({'error': '텍스트를 입력해주세요.'}), 400
    
    # 1. 설정 로드
    allowed_labels, label_name_map = get_label_config()
    calibration_map = get_calibration_map()
    conflict_axis_map = get_conflict_axis_map()
    vector_searcher = get_vector_searcher()
    
    # 2. LLM 클라이언트 (자동 모드)
    llm = None
    if mode == 'auto':
        try:
            llm = create_opencode_client()
        except Exception as e:
            return jsonify({'error': 'LLM 클라이언트 생성 실패: {}'.format(str(e))}), 500
    
    # 3. 하이브리드 파이프라인 실행
    try:
        pipeline_output = run_extraction_pipeline(
            user_input=user_input,
            label_schema={'labels': [{'micro_labels': list(allowed_labels)}]},
            conflict_axis_map=conflict_axis_map,
            llm=llm,
            calibration_map=calibration_map,
            vector_searcher=vector_searcher
        )
        extracted = pipeline_output['extracted']
        meta = pipeline_output['meta']
    except Exception as e:
        return jsonify({'error': '파이프라인 실행 실패: {}'.format(str(e))}), 500
    
    # 4. Trait 추론
    micro_labels_for_engine = []
    for s in extracted.get('sentences', []):
        for l in s.get('labels', []):
            micro_labels_for_engine.append({
                'label_id': l['label_id'],
                'label_name': l.get('reason', ''),
                'macro_category': get_macro_category(l['label_id']),
                'confidence': l['confidence']
            })
    
    engine = get_engine()
    trait_result = engine.process(micro_labels_for_engine)
    trait_name_map = get_trait_name_map()
    
    # 5. 상세 정보 구성
    primary_trait_id = trait_result['primary']
    primary_trait_type = trait_result.get('primary_type', 'positive')
    primary_details = get_trait_details(primary_trait_id)
    
    # 중요 라벨 (상위 5개)
    top_labels = sorted(micro_labels_for_engine, key=lambda x: x['confidence'], reverse=True)[:5]
    important_labels = []
    for l in top_labels:
        d = get_label_details(l['label_id'])
        important_labels.append({
            'label_id': l['label_id'],
            'name': d.get('name', ''),
            'definition': d.get('definition', ''),
            'confidence': l['confidence'],
            'macro_category': l['macro_category']
        })
    
    # Trait 퍼센티지
    trait_percentages = []
    for t in trait_result.get('sorted_trait_list', []):
        trait_percentages.append({
            'trait_id': t[0],
            'name': trait_name_map.get(t[0], 'Unknown'),
            'percentage': t[1],
            'type': t[3] if len(t) > 3 else 'positive'
        })
    
    # 부정 Trait
    negative_traits = []
    for n in trait_result.get('negative_traits', []):
        negative_traits.append({
            'trait_id': n['trait_id'],
            'name': trait_name_map.get(n['trait_id'], 'Unknown'),
            'severity': n['severity']
        })
    
    # 6. Vector DB 결과 (표시용)
    vector_results = []
    try:
        vout = vector_searcher.search_with_threshold(user_input, k=15, expand=True)
        vector_results = vout.get('results', [])
    except:
        pass
    
    # 7. 디버그 정보
    top_label = 'None'
    top_conf = 0.0
    if vector_results:
        top_label = vector_results[0]['label_id']
        top_conf = vector_results[0]['confidence']
    
    debug_info = [
        {'step': 1, 'name': 'Vector DB 검색', 'input': user_input[:80],
         'output': 'Top: {} ({:.3f})'.format(top_label, top_conf),
         'details': meta.get('vector_reason', '')},
        {'step': 2, 'name': 'LLM 호출' if meta.get('used_llm') else 'Vector DB 직접 라벨링',
         'input': 'Vector DB 결과 활용', 'output': 'LLM used: {}'.format(meta.get('used_llm')),
         'details': 'vector_only: {}'.format(meta.get('vector_only'))},
        {'step': 3, 'name': 'Calibration', 'input': 'raw confidence',
         'output': 'calibrated', 'details': 'factor: {}'.format(calibration_map.get('default', 0.88))},
        {'step': 4, 'name': 'Trait 추론', 'input': '{} labels'.format(len(micro_labels_for_engine)),
         'output': 'Primary: {}'.format(primary_trait_id), 'details': 'Confidence: {:.3f}'.format(trait_result['confidence'])}
    ]
    
    # 8. 최종 응답
    response = {
        'success': True,
        'input_text': user_input,
        'mode': mode,
        'llm_response': json.dumps(extracted, ensure_ascii=False, indent=2),
        'extracted_labels': extracted,
        'trait_result': {
            'primary': primary_trait_id,
            'primary_type': primary_trait_type,
            'primary_name': primary_details.get('name', '') if primary_details else '',
            'primary_description': primary_details.get('description', '') if primary_details else '',
            'strengths': primary_details.get('strengths', []) if primary_details else [],
            'risks': primary_details.get('risks', []) if primary_details else [],
            'secondary': trait_result.get('secondary', []),
            'confidence': trait_result['confidence'],
            'evidence': trait_result.get('evidence', {}),
            'trait_percentages': trait_percentages,
            'negative_traits': negative_traits
        },
        'important_labels': important_labels,
        'vector_results': vector_results,
        'vector_meta': {
            'vector_only': meta.get('vector_only', False),
            'vector_reason': meta.get('vector_reason', ''),
            'used_llm': meta.get('used_llm', False)
        },
        'debug_info': debug_info
    }
    
    # 9. 결과 저장 (로그인 사용자)
    user_id = session.get('user_id')
    if user_id:
        try:
            save_analysis_result(
                user_id, user_input,
                json.dumps(response, ensure_ascii=False),
                json.dumps(trait_result, ensure_ascii=False)
            )
            if session.get('username'):
                save_analysis_metadata(session.get('username'), response)
        except Exception as e:
            print('결과 저장 실패: {}'.format(e))
    
    return jsonify(response)

@app.route('/api/labels', methods=['GET'])
def get_all_labels():
    """전체 라벨 목록 반환"""
    allowed_labels, label_name_map = get_label_config()
    labels = [{'id': k, 'name': v} for k, v in label_name_map.items()]
    return jsonify({'labels': labels})

@app.route('/api/traits', methods=['GET'])
def get_all_traits():
    """전체 Trait 목록 반환"""
    trait_map = get_trait_name_map()
    traits = [{'id': k, 'name': v} for k, v in trait_map.items()]
    return jsonify({'traits': traits})

@app.route('/api/trait-examples', methods=['GET'])
def get_trait_examples():
    """Trait별 테스트 예제 반환 (필터링 지원)"""
    import random
    
    trait_filter = request.args.get('trait')
    category = request.args.get('category')
    
    try:
        with open('data/test/trait_examples.json', 'r', encoding='utf-8') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        return jsonify({'error': 'Test file not found'}), 404
    
    examples = test_data.get('examples', [])
    
    # 필터링
    if trait_filter:
        examples = [e for e in examples if e.get('trait_id') == trait_filter]
    elif category:
        examples = [e for e in examples if e.get('category') == category]
    
    # 랜덤 순서
    random.shuffle(examples)
    
    return jsonify({'examples': examples, 'total': len(examples)})

@app.route('/api/random-examples', methods=['GET'])
def get_random_examples():
    """테스트 데이터에서 전체 예제 반환 (랜덤 순서)"""
    import random
    
    with open('data/test/test_cases_v1.json', 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    cases = test_data['evaluation_cases']
    random.shuffle(cases)
    
    examples = []
    for case in cases:
        examples.append({
            'case_id': case['case_id'],
            'raw_text': case['raw_text'],
            'expected_labels': [ml['label_id'] for ml in case.get('expected_micro_labels', [])],
            'expected_result': case.get('expected_result', {})
        })
    
    return jsonify({'examples': examples, 'total': len(examples)})

@app.route('/api/test/<test_type>', methods=['GET'])
def get_test(test_type):
    """테스트 데이터 반환"""
    test_files = {
        'quiz': 'data/test/quiz_questions.json',
        'situation': 'data/test/situation_cards.json',
        'hybrid': 'data/test/hybrid_tests.json',
        'negative': 'data/test/negative_tests.json'
    }
    
    if test_type not in test_files:
        return jsonify({'error': 'Invalid test type'}), 400
    
    try:
        with open(test_files[test_type], 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        return jsonify(test_data)
    except FileNotFoundError:
        return jsonify({'error': f'Test file not found: {test_files[test_type]}'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format'}), 500

@app.route('/api/test/submit', methods=['POST'])
def submit_test():
    """테스트 결과 처리 및 Trait 분석"""
    data = request.get_json()
    test_type = data.get('test_type')
    answers = data.get('answers', [])
    test_data = data.get('test_data', {})
    
    if not answers:
        return jsonify({'error': 'No answers provided'}), 400
    
    # 답변에서 라벨 수집
    collected_labels = []
    
    for answer in answers:
        question_id = answer.get('question_id')
        answer_data = answer.get('answer', {})
        
        if test_type == 'quiz':
            # 선택형: 선택된 옵션의 traits/labels 사용
            option_id = answer_data.get('option_id')
            for q in test_data.get('questions', []):
                if q['id'] == question_id:
                    for opt in q.get('options', []):
                        if opt['id'] == option_id:
                            labels = opt.get('labels', [])
                            for label in labels:
                                if label.startswith('N'):
                                    collected_labels.append({
                                        'label_id': label,
                                        'confidence': 0.9,
                                        'macro_category': 'negative'
                                    })
                                else:
                                    collected_labels.append({
                                        'label_id': label,
                                        'confidence': 0.85,
                                        'macro_category': 'positive'
                                    })
                            break
                    break
                    
        elif test_type == 'situation':
            # 서술형: 텍스트에서 키워드 기반 라벨 추출 (간단한 휴리스틱)
            text = answer_data.get('text', '')
            label_keywords = {
                'M11-01': ['듣', '경청', '의견', '공유'],
                'M12-01': ['감정', '배려', '신경', '걱정'],
                'M15-01': ['함께', '팀', '공동', '협력'],
                'M10-01': ['결정', '판단', '선택', '지시'],
                'M01-04': ['비전', '방향', '앞날', '미래'],
                'M02-01': ['성장', '발전', '배우', '배움'],
                'M07-02': ['피드백', '코칭', '지적', '평가'],
                'M34-01': ['데이터', '분석', '수치', '근거']
            }
            for label_id, keywords in label_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        collected_labels.append({
                            'label_id': label_id,
                            'confidence': 0.7,
                            'macro_category': 'positive'
                        })
                        break
                        
        elif test_type == 'hybrid':
            # 복합형: 선택된 옵션의 traits/labels 사용
            option_id = answer_data.get('option_id')
            for t in test_data.get('tests', []):
                if t['id'] == question_id:
                    for phase in t.get('phases', []):
                        for opt in phase.get('options', []):
                            if opt['id'] == option_id:
                                labels = opt.get('labels', [])
                                for label in labels:
                                    if label.startswith('N'):
                                        collected_labels.append({
                                            'label_id': label,
                                            'confidence': 0.95,
                                            'macro_category': 'negative'
                                        })
                                    else:
                                        collected_labels.append({
                                            'label_id': label,
                                            'confidence': 0.9,
                                            'macro_category': 'positive'
                                        })
                                break
                    break
                    
        elif test_type == 'negative':
            # 부정 탐지: 올바른 선택지에 부정 라벨 포함 여부
            option_id = answer_data.get('option_id')
            for q in test_data.get('questions', []):
                if q['id'] == question_id:
                    for opt in q.get('options', []):
                        if opt['id'] == option_id:
                            if opt.get('negative'):
                                # 부정 선택지 선택 시 부정 Trait 증가
                                labels = opt.get('labels', [])
                                for label in labels:
                                    collected_labels.append({
                                        'label_id': label,
                                        'confidence': 0.95,
                                        'macro_category': 'negative'
                                    })
                            else:
                                # 정상 선택지
                                if opt.get('labels'):
                                    for label in opt['labels']:
                                        if not label.startswith('N'):
                                            collected_labels.append({
                                                'label_id': label,
                                                'confidence': 0.8,
                                                'macro_category': 'positive'
                                            })
                            break
                    break
    
    # Trait 분석 수행
    engine = get_engine()
    
    # Macro category 매핑
    for label in collected_labels:
        label['label_name'] = label.get('label_id', '')
        label['definition'] = ''
    
    trait_result = engine.process(collected_labels)
    trait_name_map = get_trait_name_map()
    
    # 결과 구성
    total_questions = len(answers)
    trait_percentages = [
        {
            'trait_id': t,
            'name': trait_name_map.get(t, 'Unknown'),
            'percentage': pct
        }
        for t, pct, _ in trait_result.get('sorted_trait_list', [])
    ]
    
    primary_trait = trait_result.get('primary', 'T01')
    primary_details = get_trait_details(primary_trait)
    
    negative_traits = trait_result.get('negative_traits', [])
    negative_traits_with_names = [
        {
            'trait_id': n['trait_id'],
            'name': trait_name_map.get(n['trait_id'], 'Unknown'),
            'severity': n['severity']
        }
        for n in negative_traits
    ]
    
    return jsonify({
        'success': True,
        'test_type': test_type,
        'total_questions': total_questions,
        'answered_questions': len(answers),
        'primary_trait': {
            'trait_id': primary_trait,
            'name': primary_details.get('name', 'Unknown') if primary_details else 'Unknown',
            'description': primary_details.get('description', '') if primary_details else ''
        },
        'trait_percentages': trait_percentages,
        'strengths': primary_details.get('strengths', []) if primary_details else [],
        'risks': primary_details.get('risks', []) if primary_details else [],
        'negative_traits': negative_traits_with_names,
        'answers': answers
    })

@app.route('/api/test/save', methods=['POST'])
def save_test_result():
    """테스트 결과 저장"""
    data = request.get_json()
    
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    results_dir = 'data/test_results'
    os.makedirs(results_dir, exist_ok=True)
    
    filename = f'{results_dir}/result_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return jsonify({
        'success': True,
        'filename': filename
    })

@app.route('/api/settings/debug-status', methods=['GET'])
def debug_status():
    """디버그 모드 상태 확인"""
    is_debug = os.getenv('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
    return jsonify({'debug': is_debug})

@app.route('/api/settings/save', methods=['POST'])
def save_settings():
    """API 설정 저장 (.env 파일 업데이트)"""
    data = request.get_json()
    opencode_key = data.get('opencode_api_key', '')
    
    if not opencode_key:
        return jsonify({'success': False, 'message': 'API 키가 없습니다.'})
    
    # .env 파일 업데이트
    env_path = '.env'
    env_lines = []
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()
    
    # 기존 OPENCODE_API_KEY 라인 찾아서 교체 또는 추가
    found = False
    for i, line in enumerate(env_lines):
        if line.startswith('OPENCODE_API_KEY='):
            env_lines[i] = f'OPENCODE_API_KEY={opencode_key}\n'
            found = True
            break
    
    if not found:
        env_lines.append(f'OPENCODE_API_KEY={opencode_key}\n')
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(env_lines)
    
    # 환경변수 즉시 반영
    os.environ['OPENCODE_API_KEY'] = opencode_key
    
    return jsonify({'success': True, 'message': 'API 키가 저장되었습니다.'})

if __name__ == '__main__':
    import os
    os.environ['WERKZEUG_SERVER_TIMEOUT'] = '900'  # 15분 타임아웃
    
    is_debug = os.getenv('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
    
    print("=" * 60)
    print("리더십 분석 시스템 웹 서버 시작")
    print(f"Debug 모드: {'ON' if is_debug else 'OFF'}")
    print("http://localhost:5000")
    print("=" * 60)
    app.run(debug=is_debug, host='0.0.0.0', port=5000)
