"""Test routes"""
from flask import Blueprint, request, jsonify
import json
import os
import random
from src.config import get_engine, get_trait_name_map, get_trait_details

test_bp = Blueprint('test', __name__)

@test_bp.route('/api/trait-examples', methods=['GET'])
def get_trait_examples():
    trait_filter = request.args.get('trait')
    category = request.args.get('category')
    
    try:
        with open('data/test/trait_examples.json', 'r', encoding='utf-8') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        return jsonify({'error': 'Test file not found'}), 404
    
    examples = test_data.get('examples', [])
    
    if trait_filter:
        examples = [e for e in examples if e.get('trait_id') == trait_filter]
    elif category:
        examples = [e for e in examples if e.get('category') == category]
    
    random.shuffle(examples)
    return jsonify({'examples': examples, 'total': len(examples)})

@test_bp.route('/api/random-examples', methods=['GET'])
def get_random_examples():
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

@test_bp.route('/api/test/<test_type>', methods=['GET'])
def get_test(test_type):
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

@test_bp.route('/api/test/submit', methods=['POST'])
def submit_test():
    data = request.get_json()
    test_type = data.get('test_type')
    answers = data.get('answers', [])
    test_data = data.get('test_data', {})
    
    if not answers:
        return jsonify({'error': 'No answers provided'}), 400
    
    collected_labels = []
    
    for answer in answers:
        question_id = answer.get('question_id')
        answer_data = answer.get('answer', {})
        
        if test_type == 'quiz':
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
            option_id = answer_data.get('option_id')
            for q in test_data.get('questions', []):
                if q['id'] == question_id:
                    for opt in q.get('options', []):
                        if opt['id'] == option_id:
                            if opt.get('negative'):
                                labels = opt.get('labels', [])
                                for label in labels:
                                    collected_labels.append({
                                        'label_id': label,
                                        'confidence': 0.95,
                                        'macro_category': 'negative'
                                    })
                            else:
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
    
    engine = get_engine()
    trait_result = engine.process(collected_labels)
    trait_name_map = get_trait_name_map()
    
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

@test_bp.route('/api/test/save', methods=['POST'])
def save_test_result():
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