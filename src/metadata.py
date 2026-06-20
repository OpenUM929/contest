"""
메타데이터 관리 모듈 (meta.md 기반)
Phase 1: PART 1 (프로필) + PART 2 (진단 결과)
"""
import json
import os
import uuid
import threading
from datetime import datetime
from src.database import get_db

METADATA_DIR = './data/metadata'
os.makedirs(METADATA_DIR, exist_ok=True)

METADATA_FILE = os.path.join(METADATA_DIR, 'users_metadata.json')

# 파일 락을 위한 쓰레드 락
_metadata_lock = threading.Lock()

def load_metadata():
    """메타데이터 파일 로드 (쓰레드 세이프)"""
    with _metadata_lock:
        if os.path.exists(METADATA_FILE):
            try:
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # 파일이 손상된 경우 기본값 반환
                return {"version": "2026-04", "last_updated": None, "users": []}
        return {"version": "2026-04", "last_updated": None, "users": []}

def save_metadata(data):
    """메타데이터 파일 저장 (쓰레드 세이프)"""
    with _metadata_lock:
        data['last_updated'] = datetime.now().isoformat()
        # 임시 파일에 먼저 쓰고 이름 변경 (원자적 연산)
        temp_file = METADATA_FILE + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())  # 디스크에 강제 쓰기
            os.replace(temp_file, METADATA_FILE)  # 원자적 이름 변경
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e

def get_user_metadata(user_key):
    """사용자 메타데이터 조회"""
    metadata = load_metadata()
    for user in metadata.get('users', []):
        if user.get('user_key') == user_key:
            return user
    return None

def update_user_metadata(user_key, profile_data=None, test_context=None, results=None):
    """
    사용자 메타데이터 업데이트
    profile: PART 1 (인사정보)
    test_context: PART 1 (테스트 맥락)
    results: PART 2 (진단 결과)
    """
    metadata = load_metadata()
    
    user = None
    for u in metadata.get('users', []):
        if u.get('user_key') == user_key:
            user = u
            break
    
    if not user:
        user = {
            "user_id": str(uuid.uuid4()),
            "user_key": user_key,
            "created_at": datetime.now().isoformat(),
            "profile": {},
            "test_context": {},
            "results": {},
            "history": {
                "total_attempts": 0,
                "test_history": []
            }
        }
        metadata['users'].append(user)
    
    # PART 1: 프로필 업데이트
    if profile_data:
        user['profile'].update(profile_data)
    
    # PART 1: 테스트 맥락 업데이트
    if test_context:
        user['test_context'].update(test_context)
    
    # PART 2: 진단 결과 업데이트 (가장 최근)
    if results:
        attempt_number = user['history'].get('total_attempts', 0) + 1
        
        # 이력에 추가
        history_entry = {
            "attempt_number": attempt_number,
            "test_taken_at": results.get('test_taken_at', datetime.now().isoformat()),
            "primary_trait_id": results.get('primary_trait', {}).get('trait_id'),
            "primary_strength": results.get('primary_trait', {}).get('strength_normalized'),
            "negative_traits_count": len(results.get('negative_traits', [])),
            "risk_score_max": max([r.get('risk_score', 0) for r in results.get('risks', [])], default=0),
            "context_tag": results.get('context_tag', 'normal'),
            "test_type": results.get('test_type', 'choice')
        }
        
        user['history']['test_history'].append(history_entry)
        user['history']['total_attempts'] = attempt_number
        
        # 현재 결과 저장
        user['results'] = results
        user['last_analysis_at'] = datetime.now().isoformat()
    
    save_metadata(metadata)
    return user

def save_analysis_metadata(user_key, analysis_result):
    """
    분석 결과から메타데이터生成 및 저장
    analysis_result: 분석 API의 결과
    """
    # PART 2: 진단 결과 구조로 변환
    trait_result = analysis_result.get('trait_result', {})
    important_labels = analysis_result.get('important_labels', [])
    extracted_labels = analysis_result.get('extracted_labels', {})
    
    results = {
        "test_taken_at": datetime.now().isoformat(),
        
        # Primary Trait
        "primary_trait": {
            "trait_id": trait_result.get('primary'),
            "trait_name": trait_result.get('primary_name'),
            "strength_normalized": trait_result.get('confidence', 0),
            "strength_level": _get_strength_level(trait_result.get('confidence', 0)),
            "confidence": trait_result.get('confidence', 0),
            "confidence_level": _get_confidence_level(trait_result.get('confidence', 0)),
            "context_multiplier": 1.0,
            "hard_conflict_triggered": False
        },
        
        # Secondary Traits
        "secondary_traits": [],
        
        # Hybrid Traits (예정)
        "hybrid_traits": [],
        
        # Negative Traits
        "negative_traits": [],
        
        # Risks
        "risks": [],
        
        # Evidence (근거)
        "evidence": _build_evidence(important_labels),
        
        # Resolution
        "resolution": {
            "conflict_detected": False,
            "suspended_judgment": False
        },
        
        # Label distribution
        "label_distribution": _build_label_distribution(extracted_labels)
    }
    
    # Secondary Traits
    if trait_result.get('secondary'):
        for i, st in enumerate(trait_result.get('secondary', [])):
            results['secondary_traits'].append({
                "trait_id": st,
                "strength_level": "Moderate",
                "confidence_level": "Medium"
            })
    
    # Negative Traits
    if trait_result.get('negative_traits'):
        for nt in trait_result.get('negative_traits', []):
            results['negative_traits'].append({
                "trait_id": nt.get('trait_id', 'T_RISK'),
                "trait_name": nt.get('name', 'Negative Trait'),
                "severity_score": nt.get('severity', 0),
                "severity_level": _get_severity_level(nt.get('severity', 0))
            })
    
    return update_user_metadata(user_key, results=results)

def _get_strength_level(confidence):
    try:
        conf = float(confidence) if not isinstance(confidence, (int, float)) else confidence
    except (TypeError, ValueError):
        return "Weak"
    if conf >= 0.8: return "Strong"
    if conf >= 0.5: return "Moderate"
    return "Weak"

def _get_confidence_level(confidence):
    try:
        conf = float(confidence) if not isinstance(confidence, (int, float)) else confidence
    except (TypeError, ValueError):
        return "Low"
    if conf >= 0.75: return "High"
    if conf >= 0.45: return "Medium"
    return "Low"

def _get_severity_level(severity):
    if severity >= 0.7: return "high"
    if severity >= 0.4: return "medium"
    return "low"

def _build_evidence(important_labels):
    """Evidence (근거) 생성"""
    evidence = []
    for label in important_labels:
        evidence.append({
            "label_id": label.get('label_id'),
            "label_type": "M" if not label.get('label_id', '').startswith('N') else "N",
            "role": "REQ",
            "nlp_confidence": label.get('confidence', 0),
            "is_critical": False
        })
    return evidence

def _build_label_distribution(extracted_labels):
    """Label 분포 통계"""
    positive = 0
    negative = 0
    
    sentences = extracted_labels.get('sentences', [])
    for sentence in sentences:
        for label in sentence.get('labels', []):
            lid = label.get('label_id', '')
            if lid.startswith('N'):
                negative += 1
            elif lid.startswith('M'):
                positive += 1
    
    total = positive + negative
    return {
        "positive_count": positive,
        "negative_count": negative,
        "positive_rate": round(positive / total * 100, 1) if total > 0 else 0
    }

def get_user_profile(user_key):
    """사용자 프로필 조회"""
    user = get_user_metadata(user_key)
    if user:
        return user.get('profile', {})
    return {}

def get_user_results(user_key):
    """사용자 진단 결과 조회"""
    user = get_user_metadata(user_key)
    if user:
        return user.get('results', {})
    return {}

def get_user_history(user_key):
    """사용자 이력 조회"""
    user = get_user_metadata(user_key)
    if user:
        return user.get('history', {})
    return {}

def calculate_trait_delta(user_key):
    """Trait 변화량 (Delta) 계산 - Phase 2"""
    user = get_user_metadata(user_key)
    if not user:
        return []
    
    history = user.get('history', {}).get('test_history', [])
    if len(history) < 2:
        return []
    
    deltas = []
    # 최근 2회 비교
    prev = history[-2]
    curr = history[-1]
    
    if prev.get('primary_trait_id') == curr.get('primary_trait_id'):
        delta = curr.get('primary_strength', 0) - prev.get('primary_strength', 0)
        deltas.append({
            "trait_id": curr.get('primary_trait_id'),
            "prev_strength": prev.get('primary_strength', 0),
            "curr_strength": curr.get('primary_strength', 0),
            "delta": round(delta, 3),
            "delta_pct": round((delta / prev.get('primary_strength', 1)) * 100, 1) if prev.get('primary_strength', 0) > 0 else 0,
            "trend": "improving" if delta > 0.05 else ("declining" if delta < -0.05 else "stable")
        })
    
    return deltas

def calculate_trait_trend(user_key):
    """Trait 추세 계산 (3회 이상) - Phase 2"""
    user = get_user_metadata(user_key)
    if not user:
        return []
    
    history = user.get('history', {}).get('test_history', [])
    if len(history) < 3:
        return []
    
    # 최근 3회 데이터
    recent = history[-3:]
    
    # 각 Trait별 추이 계산
    trait_strengths = {}
    for attempt in recent:
        trait_id = attempt.get('primary_trait_id')
        strength = attempt.get('primary_strength', 0)
        if trait_id not in trait_strengths:
            trait_strengths[trait_id] = []
        trait_strengths[trait_id].append(strength)
    
    trends = []
    for trait_id, strengths in trait_strengths.items():
        if len(strengths) >= 2:
            delta = strengths[-1] - strengths[0]
            avg = sum(strengths) / len(strengths)
            trends.append({
                "trait_id": trait_id,
                "first_strength": strengths[0],
                "last_strength": strengths[-1],
                "avg_strength": round(avg, 3),
                "delta": round(delta, 3),
                "trend": "improving" if delta > 0.1 else ("declining" if delta < -0.1 else "stable"),
                "sessions_compared": len(strengths)
            })
    
    return trends

def save_program_impact(user_key, program_id, pre_test_session_id, post_test_session_id):
    """프로그램 효과 저장 - Phase 2"""
    metadata = load_metadata()
    
    user = None
    for u in metadata.get('users', []):
        if u.get('user_key') == user_key:
            user = u
            break
    
    if not user:
        return None
    
    if 'program_impact' not in user.get('history', {}):
        user.setdefault('history', {}).setdefault('program_impact', [])
    
    # Pre/Post 테스트 결과 조회
    history = user.get('history', {}).get('test_history', [])
    pre_result = next((h for h in history if h.get('attempt_number') == pre_test_session_id), None)
    post_result = next((h for h in history if h.get('attempt_number') == post_test_session_id), None)
    
    if pre_result and post_result:
        pre_strength = pre_result.get('primary_strength', 0)
        post_strength = post_result.get('primary_strength', 0)
        actual_change = post_strength - pre_strength
        
        impact = {
            "program_id": program_id,
            "pre_test_session_id": pre_test_session_id,
            "post_test_session_id": post_test_session_id,
            "target_trait_id": post_result.get('primary_trait_id'),
            "target_strength_change": 0.15,  # 목표값 (설정 필요)
            "actual_strength_change": round(actual_change, 3),
            "negative_reduction": 0,
            "goal_achieved": actual_change >= 0.15,
            "effect_size": 0  # Cohen's d 계산 필요
        }
        
        user['history']['program_impact'].append(impact)
        save_metadata(metadata)
        return impact
    
    return None


# ===== Phase 3: 집단 분석 (Cohort, Gap Analysis) =====

def analyze_cohort(cohort_type, cohort_value, date_range=None):
    """집단 분석 (Cohort) - Phase 3"""
    metadata = load_metadata()
    users = metadata.get('users', [])
    
    # 필터링
    cohort_users = []
    for user in users:
        profile = user.get('profile', {})
        
        if cohort_type == 'department' and profile.get('department') == cohort_value:
            cohort_users.append(user)
        elif cohort_type == 'position' and profile.get('position') == cohort_value:
            cohort_users.append(user)
        elif cohort_type == 'job_level' and profile.get('job_level') == cohort_value:
            cohort_users.append(user)
        elif cohort_type == 'team' and profile.get('team') == cohort_value:
            cohort_users.append(user)
        elif cohort_type == 'industry' and profile.get('industry') == cohort_value:
            cohort_users.append(user)
    
    if not cohort_users:
        return None
    
    # Trait 분포 계산
    trait_counts = {}
    total_strength = 0
    total_confidence = 0
    valid_count = 0
    negative_count = 0
    
    for user in cohort_users:
        results = user.get('results', {})
        primary = results.get('primary_trait', {})
        
        if primary.get('trait_id'):
            trait_id = primary['trait_id']
            trait_counts[trait_id] = trait_counts.get(trait_id, 0) + 1
            
            strength = primary.get('strength_normalized', 0)
            confidence = primary.get('confidence', 0)
            
            if strength > 0:
                total_strength += strength
                total_confidence += confidence
                valid_count += 1
        
        # Negative Trait
        negatives = results.get('negative_traits', [])
        negative_count += len(negatives)
    
    # 분포 통계
    total_users = len(cohort_users)
    trait_distribution = []
    for trait_id, count in trait_counts.items():
        trait_distribution.append({
            "trait_id": trait_id,
            "primary_count": count,
            "primary_ratio": round(count / total_users, 3) if total_users > 0 else 0
        })
    trait_distribution.sort(key=lambda x: x['primary_count'], reverse=True)
    
    # Dominant Trait
    dominant_trait = trait_distribution[0]['trait_id'] if trait_distribution else None
    
    # Negative Trait
    negative_traits_count = {}
    for user in cohort_users:
        results = user.get('results', {})
        for nt in results.get('negative_traits', []):
            tid = nt.get('trait_id', 'T_RISK')
            negative_traits_count[tid] = negative_traits_count.get(tid, 0) + 1
    
    dominant_negative = max(negative_traits_count.items(), key=lambda x: x[1])[0] if negative_traits_count else None
    
    # 리스크 비율
    users_with_risk = sum(1 for u in cohort_users if u.get('results', {}).get('negative_traits'))
    risk_prevalence = round(users_with_risk / total_users, 3) if total_users > 0 else 0
    
    return {
        "cohort_id": f"COHORT-{cohort_type}-{cohort_value}",
        "cohort_type": cohort_type,
        "cohort_name": f"{cohort_type}: {cohort_value}",
        "member_count": total_users,
        "trait_distribution": trait_distribution,
        "dominant_trait": dominant_trait,
        "dominant_negative": dominant_negative,
        "risk_prevalence": risk_prevalence,
        "avg_confidence": round(total_confidence / valid_count, 3) if valid_count > 0 else 0,
        "avg_strength": round(total_strength / valid_count, 3) if valid_count > 0 else 0
    }

def analyze_gap(cohort_type, cohort_value):
    """리더십 갭 분석 - Phase 3"""
    cohort = analyze_cohort(cohort_type, cohort_value)
    if not cohort:
        return None
    
    # 전체 평균 비율 계산
    all_users = get_all_users_summary().get('users', [])
    if not all_users:
        return None
    
    # 전체 Trait 비율
    total_traits = {}
    for u in all_users:
        pt = u.get('primary_trait')
        if pt:
            total_traits[pt] = total_traits.get(pt, 0) + 1
    
    total_count = sum(total_traits.values())
    avg_ratios = {t: c/total_count for t, c in total_traits.items()} if total_count > 0 else {}
    
    # 갭 분석
    cohort_dist = {t['trait_id']: t['primary_ratio'] for t in cohort.get('trait_distribution', [])}
    
    missing_traits = []
    underrepresented_traits = []
    overrepresented_traits = []
    
    all_trait_ids = list(avg_ratios.keys())
    for trait_id in all_trait_ids:
        cohort_ratio = cohort_dist.get(trait_id, 0)
        avg_ratio = avg_ratios.get(trait_id, 0)
        
        # 해당 Trait이Cohort에 없으면 Missing
        if cohort_ratio == 0:
            missing_traits.append(trait_id)
        # Cohort 비율이 평균의 50% 미만
        elif avg_ratio > 0 and cohort_ratio < avg_ratio * 0.5:
            underrepresented_traits.append(trait_id)
        # Cohort 비율이 평균의 2배 이상
        elif avg_ratio > 0 and cohort_ratio > avg_ratio * 2:
            overrepresented_traits.append(trait_id)
    
    # 부정 Trait 집중 위험
    negative_cluster_risk = False
    if cohort.get('risk_prevalence', 0) > 0.3:
        negative_cluster_risk = True
    
    return {
        "missing_traits": missing_traits,
        "underrepresented_traits": underrepresented_traits,
        "overrepresented_traits": overrepresented_traits,
        "negative_cluster_risk": negative_cluster_risk,
        "recommended_programs": _recommend_programs(missing_traits, underrepresented_traits)
    }

def _recommend_programs(missing_traits, underrepresented_traits):
    """갭 해소를 위한 추천 프로그램"""
    recommendations = []
    
    trait_program_map = {
        'T01': 'PROG-VISION',
        'T02': 'PROG-RELATIONSHIP',
        'T03': 'PROG-CHANGE',
        'T04': 'PROG-DECISION',
        'T05': 'PROG-DATA',
        'T06': 'PROG-PROCESS',
        'T07': 'PROG-DEVELOPMENT',
        'T08': 'PROG-EMOTIONAL',
        'T09': 'PROG-INSPIRATION',
        'T10': 'PROG-GOAL',
        'T11': 'PROG-COMM',
        'T12': 'PROG-ADAPT'
    }
    
    for trait in missing_traits + underrepresented_traits:
        if trait in trait_program_map:
            recommendations.append(trait_program_map[trait])
    
    return list(set(recommendations))[:5]  # 최대 5개


# ===== Phase 4: 인사이트 트리거 =====

def generate_insights(user_key):
    """자동 인사이트 생성 - Phase 4"""
    user = get_user_metadata(user_key)
    if not user:
        return []
    
    insights = []
    results = user.get('results', {})
    history = user.get('history', {})
    
    # INS-01: 강점 부각
    primary = results.get('primary_trait', {})
    if primary.get('strength_level') == 'Strong' and primary.get('confidence_level') == 'High':
        insights.append({
            "id": "INS-01",
            "type": "강점 부각",
            "message": f"당신의 {primary.get('trait_name')} 성향이 매우 강하게 나타납니다.",
            "priority": "high"
        })
    
    # INS-02: 리스크 경고
    risks = results.get('risks', [])
    for risk in risks:
        if risk.get('severity') == 'high':
            insights.append({
                "id": "INS-02",
                "type": "리스크 경고",
                "message": f"{risk.get('risk_name')}이 감지되었습니다. 주의가 필요합니다.",
                "priority": "critical"
            })
    
    # INS-03: 성향 충돌
    resolution = results.get('resolution', {})
    if resolution.get('conflict_detected'):
        insights.append({
            "id": "INS-03",
            "type": "성향 충돌 알림",
            "message": "복합적 성향이 감지되어 결과 해석에 주의가 필요합니다.",
            "priority": "medium"
        })
    
    # INS-04: 성장 축하 (Delta 기반)
    deltas = calculate_trait_delta(user_key)
    for delta in deltas:
        if delta.get('trend') == 'improving' and delta.get('delta_pct', 0) > 15:
            insights.append({
                "id": "INS-04",
                "type": "성장 축하",
                "message": f"지난 응시 대비 {delta.get('trait_id')} 성향이 {delta.get('delta_pct')}% 강화되었습니다.",
                "priority": "high"
            })
    
    # INS-05: 코칭 제안
    negatives = results.get('negative_traits', [])
    if negatives and len(negatives) > 0:
        insights.append({
            "id": "INS-05",
            "type": "코칭 제안",
            "message": f"부정적 패턴({len(negatives)}개)이 감지되었습니다. 전문 코칭을 권장합니다.",
            "priority": "medium"
        })
    
    return insights

def generate_cohort_insights(cohort_type, cohort_value):
    """집단 인사이트 생성 - Phase 4"""
    cohort = analyze_cohort(cohort_type, cohort_value)
    gap = analyze_gap(cohort_type, cohort_value)
    
    if not cohort:
        return []
    
    insights = []
    
    # CIN-01: 리더십 공백 경고
    if gap and gap.get('missing_traits'):
        insights.append({
            "id": "CIN-01",
            "type": "리더십 공백 경고",
            "message": f"조직 내 {', '.join(gap['missing_traits'])} 리더십이 부족합니다.",
            "priority": "critical"
        })
    
    # CIN-02: 권위주의 집중 경보
    if cohort.get('dominant_negative') in ['T10', 'T11', 'T_RISK_AVOIDANT']:
        insights.append({
            "id": "CIN-02",
            "type": "집중 경보",
            "message": "부정적 성향이 집단에 집중되어 있습니다. 심리적 안전감 관리가 필요합니다.",
            "priority": "high"
        })
    
    # CIN-03: 혁신 역량 부족
    if gap and gap.get('underrepresented_traits'):
        underrepresented = gap['underrepresented_traits']
        if 'T03' in underrepresented or 'T06' in underrepresented:
            insights.append({
                "id": "CIN-03",
                "type": "역량 부족",
                "message": "혁신·실행 리더십이 부족합니다. 변화 추진 역량 강화가 필요합니다.",
                "priority": "medium"
            })
    
    return insights

def get_all_users_summary():
    """전체 사용자 요약 (집단 분석용)"""
    metadata = load_metadata()
    users = metadata.get('users', [])
    
    summary = {
        "total_users": len(users),
        "users": []
    }
    
    for user in users:
        profile = user.get('profile', {})
        results = user.get('results', {})
        primary = results.get('primary_trait', {})
        
        summary['users'].append({
            "user_key": user.get('user_key'),
            "department": profile.get('department'),
            "position": profile.get('position'),
            "job_level": profile.get('job_level'),
            "primary_trait": primary.get('trait_id'),
            "primary_trait_name": primary.get('trait_name'),
            "strength": primary.get('strength_normalized'),
            "confidence": primary.get('confidence'),
            "last_analysis": user.get('last_analysis_at')
        })
    
    return summary