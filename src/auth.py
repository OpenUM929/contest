"""
Authentication Module - SHA-256 Hash Based
"""
import hashlib
import json
import secrets
import sqlite3
from datetime import datetime
from src.database import get_db, init_db

def generate_salt():
    """랜덤 Salt 생성"""
    return secrets.token_hex(32)

def hash_password(password, salt):
    """SHA-256 기반 비밀번호 해시 (PBKDF2 스타일)"""
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )
    return key.hex()

def create_user(username, password):
    """회원가입"""
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        salt = generate_salt()
        password_hash = hash_password(password, salt)
        
        cursor.execute(
            'INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)',
            (username, password_hash, salt)
        )
        conn.commit()
        return {'success': True, 'message': '회원가입 성공'}
    except sqlite3.IntegrityError:
        return {'success': False, 'message': '이미 존재하는 아이디입니다.'}
    except Exception as e:
        return {'success': False, 'message': str(e)}
    finally:
        conn.close()

def verify_user(username, password):
    """로그인 검증"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT id, password_hash, salt FROM users WHERE username = ?',
        (username,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {'success': False, 'message': '존재하지 않는 아이디입니다.'}
    
    password_hash = hash_password(password, row['salt'])
    
    if password_hash == row['password_hash']:
        # 마지막 로그인 시간 업데이트
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET last_login = ? WHERE id = ?',
            (datetime.now().isoformat(), row['id'])
        )
        conn.commit()
        conn.close()
        
        return {'success': True, 'user_id': row['id'], 'username': username}
    else:
        return {'success': False, 'message': '비밀번호가 일치하지 않습니다.'}

def get_user_by_id(user_id):
    """사용자 정보 조회"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, created_at, last_login FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def save_analysis_result(user_id, input_text, result_json, trait_result):
    """분석 결과 저장"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO analysis_results (user_id, input_text, result_json, trait_result) VALUES (?, ?, ?, ?)',
        (user_id, input_text, result_json, trait_result)
    )
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()
    
    return result_id

def get_user_analysis_results(user_id, limit=50):
    """사용자의 분석 결과 조회"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, input_text, trait_result, created_at 
        FROM analysis_results 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (user_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_all_analysis_results():
    """전체 분석 결과 조회 (대시보드용)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ar.id, ar.input_text, ar.result_json, ar.trait_result, ar.created_at, u.username
        FROM analysis_results ar
        JOIN users u ON ar.user_id = u.id
        ORDER BY ar.created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_dashboard_stats():
    """대시보드 통계 데이터"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 총 사용자 수
    cursor.execute('SELECT COUNT(*) as count FROM users')
    total_users = cursor.fetchone()['count']
    
    # 총 분석 수
    cursor.execute('SELECT COUNT(*) as count FROM analysis_results')
    total_analyses = cursor.fetchone()['count']
    
    # 오늘 분석 수
    cursor.execute('''
        SELECT COUNT(*) as count FROM analysis_results 
        WHERE DATE(created_at) = DATE('now')
    ''')
    today_analyses = cursor.fetchone()['count']
    
    #昨일 분석 수
    cursor.execute('''
        SELECT COUNT(*) as count FROM analysis_results 
        WHERE DATE(created_at) = DATE('now', '-1 day')
    ''')
    yesterday_analyses = cursor.fetchone()['count']
    
    # 이번 주 분석 수
    cursor.execute('''
        SELECT COUNT(*) as count FROM analysis_results 
        WHERE DATE(created_at) >= DATE('now', '-7 days')
    ''')
    week_analyses = cursor.fetchone()['count']
    
    # 평균 분석 수/일
    cursor.execute('''
        SELECT COUNT(*) as total, 
               MIN(DATE(created_at)) as first_date,
               MAX(DATE(created_at)) as last_date
        FROM analysis_results
    ''')
    stats = cursor.fetchone()
    if stats['total'] > 0 and stats['first_date'] and stats['last_date']:
        from datetime import datetime
        first = datetime.strptime(stats['first_date'], '%Y-%m-%d')
        last = datetime.strptime(stats['last_date'], '%Y-%m-%d')
        days = (last - first).days + 1
        avg_per_day = round(stats['total'] / days, 1)
    else:
        avg_per_day = 0
    
    conn.close()
    
    return {
        'total_users': total_users,
        'total_analyses': total_analyses,
        'today_analyses': today_analyses,
        'yesterday_analyses': yesterday_analyses,
        'week_analyses': week_analyses,
        'avg_per_day': avg_per_day
    }

def get_trait_distribution():
    """Trait 분포 데이터 (대시보드)"""
    import json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT trait_result FROM analysis_results WHERE trait_result IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    
    trait_counts = {}
    for row in rows:
        if row['trait_result']:
            try:
                result = json.loads(row['trait_result'])
                if 'primary' in result and result['primary']:
                    trait = result['primary']
                    trait_counts[trait] = trait_counts.get(trait, 0) + 1
            except:
                pass
    
    return trait_counts

def get_trait_percentages():
    """Trait별 Percentage 분포 (정규화된 %)"""
    import json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT trait_result FROM analysis_results WHERE trait_result IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    
    trait_totals = {}
    total_weight = 0
    
    for row in rows:
        if row['trait_result']:
            try:
                result = json.loads(row['trait_result'])
                if 'trait_percentages' in result:
                    for tp in result['trait_percentages']:
                        trait = tp.get('trait_id', '')
                        pct = tp.get('percentage', 0)
                        if trait:
                            trait_totals[trait] = trait_totals.get(trait, 0) + pct
                            total_weight += pct
            except:
                pass
    
    if total_weight == 0:
        return []
    
    result = []
    for trait, total in trait_totals.items():
        pct = round((total / total_weight) * 100, 1)
        result.append({'trait_id': trait, 'percentage': pct})
    
    result.sort(key=lambda x: x['percentage'], reverse=True)
    return result

def get_category_distribution():
    """카테고리별 분포"""
    import json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT result_json FROM analysis_results WHERE result_json IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    
    category_counts = {}
    
    for row in rows:
        if row['result_json']:
            try:
                data = json.loads(row['result_json'])
                if 'extracted_labels' in data:
                    labels = data['extracted_labels']
                    if 'sentences' in labels:
                        for s in labels['sentences']:
                            for l in s.get('labels', []):
                                lid = l.get('label_id', '')
                                cat = 'Positive' if lid.startswith('M') else ('Negative' if lid.startswith('N') else 'Unknown')
                                category_counts[cat] = category_counts.get(cat, 0) + 1
            except:
                pass
    
    return category_counts

def get_daily_trend():
    """일별 분석 추이 (최근 14일)"""
    import json
    from datetime import datetime, timedelta
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM analysis_results
        WHERE created_at >= DATE('now', '-14 days')
        GROUP BY DATE(created_at)
        ORDER BY date
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    # 최근 14일 데이터 생성
    today = datetime.now().date()
    date_range = [(today - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
    
    result = []
    for d in date_range:
        found = False
        for row in rows:
            if row['date'] == d:
                result.append({'date': d, 'count': row['count']})
                found = True
                break
        if not found:
            result.append({'date': d, 'count': 0})
    
    return result

def get_recent_analyses(limit=10):
    """최근 분석 결과 목록"""
    import json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ar.id, ar.input_text, ar.trait_result, ar.created_at, u.username
        FROM analysis_results ar
        JOIN users u ON ar.user_id = u.id
        ORDER BY ar.created_at DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        trait_result = {}
        if row['trait_result']:
            try:
                trait_result = json.loads(row['trait_result'])
            except:
                pass
        
        results.append({
            'id': row['id'],
            'text': row['input_text'][:100] + '...' if row['input_text'] and len(row['input_text']) > 100 else row['input_text'],
            'primary_trait': trait_result.get('primary', '-'),
            'primary_name': trait_result.get('primary_name', '-'),
            'created_at': row['created_at'],
            'username': row['username']
        })
    
    return results

def get_positive_negative_ratio():
    """Positive/Negative 비율"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT result_json FROM analysis_results WHERE result_json IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    
    positive = 0
    negative = 0
    
    for row in rows:
        if row['result_json']:
            try:
                import json
                data = json.loads(row['result_json'])
                if 'extracted_labels' in data:
                    labels = data['extracted_labels']
                    if 'sentences' in labels:
                        for s in labels['sentences']:
                            for l in s.get('labels', []):
                                lid = l.get('label_id', '')
                                if lid.startswith('N'):
                                    negative += 1
                                elif lid.startswith('M'):
                                    positive += 1
            except:
                pass
    
    total = positive + negative
    if total == 0:
        return {'positive': 50, 'negative': 50}
    
    return {
        'positive': round(positive / total * 100, 1),
        'negative': round(negative / total * 100, 1)
    }

def get_negative_trait_count():
    """부정 Trait 감지 수"""
    import json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT trait_result FROM analysis_results WHERE trait_result IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    
    count = 0
    for row in rows:
        if row['trait_result']:
            try:
                result = json.loads(row['trait_result'])
                if 'negative_traits' in result and result['negative_traits']:
                    count += len(result['negative_traits'])
            except:
                pass
    
    return count

def get_top_trait():
    """가장 많은 Primary Trait"""
    import json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT trait_result FROM analysis_results WHERE trait_result IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    
    trait_counts = {}
    for row in rows:
        if row['trait_result']:
            try:
                result = json.loads(row['trait_result'])
                if 'primary' in result and result['primary']:
                    trait = result['primary']
                    trait_counts[trait] = trait_counts.get(trait, 0) + 1
            except:
                pass
    
    if not trait_counts:
        return None
    
    max_trait = max(trait_counts.items(), key=lambda x: x[1])
    total = sum(trait_counts.values())
    return {
        'trait_id': max_trait[0],
        'count': max_trait[1],
        'percentage': round(max_trait[1] / total * 100, 1)
    }

def get_dashboard_summary():
    """대시보드 요약 정보 (한 줄)"""
    import json
    from datetime import datetime
    conn = get_db()
    cursor = conn.cursor()
    
    # 총 분석 수
    cursor.execute('SELECT COUNT(*) as count FROM analysis_results')
    total_analyses = cursor.fetchone()['count']
    
    # 일 평균
    cursor.execute('''
        SELECT COUNT(*) as total, 
               MIN(DATE(created_at)) as first_date,
               MAX(DATE(created_at)) as last_date
        FROM analysis_results
    ''')
    stats = cursor.fetchone()
    if stats['total'] > 0 and stats['first_date'] and stats['last_date']:
        first = datetime.strptime(stats['first_date'], '%Y-%m-%d')
        last = datetime.strptime(stats['last_date'], '%Y-%m-%d')
        days = (last - first).days + 1
        avg_per_day = round(stats['total'] / days, 1)
    else:
        avg_per_day = 0
    
    # 어제 분석 수
    cursor.execute('''
        SELECT COUNT(*) as count FROM analysis_results 
        WHERE DATE(created_at) = DATE('now', '-1 day')
    ''')
    yesterday = cursor.fetchone()['count']
    
    # 주요 Trait
    cursor.execute('SELECT trait_result FROM analysis_results WHERE trait_result IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    
    trait_counts = {}
    for row in rows:
        if row['trait_result']:
            try:
                result = json.loads(row['trait_result'])
                if 'primary' in result and result['primary']:
                    trait = result['primary']
                    trait_counts[trait] = trait_counts.get(trait, 0) + 1
            except:
                pass
    
    top_trait = None
    if trait_counts:
        max_trait = max(trait_counts.items(), key=lambda x: x[1])
        total = sum(trait_counts.values())
        top_trait = {'trait_id': max_trait[0], 'percentage': round(max_trait[1] / total * 100, 1)}
    
    # Positive 비율
    pos_ratio = get_positive_negative_ratio()
    
    # 부정 Trait 수
    neg_count = get_negative_trait_count()
    
    # 마지막 분석 시간
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(created_at) as last_time FROM analysis_results')
    last_time = cursor.fetchone()['last_time']
    conn.close()
    
    return {
        'total_analyses': total_analyses,
        'avg_per_day': avg_per_day,
        'yesterday_analyses': yesterday,
        'top_trait': top_trait,
        'positive_rate': pos_ratio['positive'],
        'negative_trait_count': neg_count,
        'last_analysis': last_time[:10] if last_time else '-'
    }

def get_dashboard_by_period(period='all'):
    """기간별 대시보드 데이터 (일/주/月/연)"""
    import json
    from datetime import datetime, timedelta
    
    period_map = {
        'day': 1,
        'week': 7,
        'month': 30,
        'year': 365
    }
    
    days = period_map.get(period, 365)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 기간 필터 (파라미터 바인딩으로 SQL Injection 방지)
    cursor.execute('''
        SELECT trait_result, result_json, created_at
        FROM analysis_results
        WHERE created_at >= DATE('now', '-' || ? || ' days')
    ''', (days,))
    rows = cursor.fetchall()
    
    trait_counts = {}
    trait_totals = {}
    positive = 0
    negative = 0
    total_weight = 0
    negative_trait_count = 0
    
    for row in rows:
        if row['trait_result']:
            try:
                result = json.loads(row['trait_result'])
                # Primary Trait
                if 'primary' in result and result['primary']:
                    trait = result['primary']
                    trait_counts[trait] = trait_counts.get(trait, 0) + 1
                # Trait Percentages
                if 'trait_percentages' in result:
                    for tp in result['trait_percentages']:
                        trait = tp.get('trait_id', '')
                        pct = tp.get('percentage', 0)
                        if trait:
                            trait_totals[trait] = trait_totals.get(trait, 0) + pct
                            total_weight += pct
                # Negative Traits
                if 'negative_traits' in result and result['negative_traits']:
                    negative_trait_count += len(result['negative_traits'])
            except:
                pass
        
        if row['result_json']:
            try:
                data = json.loads(row['result_json'])
                if 'extracted_labels' in data:
                    labels = data['extracted_labels']
                    if 'sentences' in labels:
                        for s in labels['sentences']:
                            for l in s.get('labels', []):
                                lid = l.get('label_id', '')
                                if lid.startswith('N'):
                                    negative += 1
                                elif lid.startswith('M'):
                                    positive += 1
            except:
                pass
    
    conn.close()
    
    # Trait 분포 (count)
    trait_dist = [{'trait_id': t, 'count': c} for t, c in trait_counts.items()]
    trait_dist.sort(key=lambda x: x['count'], reverse=True)
    
    # Trait 비율 (%)
    trait_pct = []
    if total_weight > 0:
        for trait, total in trait_totals.items():
            pct = round((total / total_weight) * 100, 1)
            trait_pct.append({'trait_id': trait, 'percentage': pct})
        trait_pct.sort(key=lambda x: x['percentage'], reverse=True)
    
    # Positive/Negative
    total = positive + negative
    if total == 0:
        pos_neg = {'positive': 50, 'negative': 50}
    else:
        pos_neg = {
            'positive': round(positive / total * 100, 1),
            'negative': round(negative / total * 100, 1)
        }
    
    # 일별 추이
    if period == 'day':
        days = 7
    elif period == 'week':
        days = 28
    elif period == 'month':
        days = 90
    else:
        days = 365
    
    today = datetime.now().date()
    date_range = [(today - timedelta(days=i)).isoformat() for i in range(days-1, -1, -1)]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM analysis_results
        WHERE created_at >= DATE('now', '-{} days')
        GROUP BY DATE(created_at)
        ORDER BY date
    '''.format(days))
    trend_rows = cursor.fetchall()
    conn.close()
    
    trend_dict = {r['date']: r['count'] for r in trend_rows}
    daily_trend = [{'date': d, 'count': trend_dict.get(d, 0)} for d in date_range]
    
    # Trait별 추이 (주/月단위)
    if period == 'week':
        group_by = "strftime('%Y-%W', created_at)"
    elif period == 'month':
        group_by = "strftime('%Y-%m', created_at)"
    elif period == 'year':
        group_by = "strftime('%Y', created_at)"
    else:
        group_by = "DATE(created_at)"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT {} as period, trait_result
        FROM analysis_results
        WHERE created_at >= DATE('now', '-{} days') AND trait_result IS NOT NULL
    '''.format(group_by, days))
    period_rows = cursor.fetchall()
    conn.close()
    
    period_traits = {}
    for row in period_rows:
        period = row['period']
        if row['trait_result']:
            try:
                result = json.loads(row['trait_result'])
                if 'primary' in result and result['primary']:
                    if period not in period_traits:
                        period_traits[period] = {}
                    trait = result['primary']
                    period_traits[period][trait] = period_traits[period].get(trait, 0) + 1
            except:
                pass
    
    trait_trend = []
    for period in sorted(period_traits.keys()):
        row_data = period_traits[period]
        total_period = sum(row_data.values())
        for trait, count in row_data.items():
            trait_trend.append({
                'period': period,
                'trait_id': trait,
                'count': count,
                'percentage': round(count / total_period * 100, 1) if total_period > 0 else 0
            })
    
    return {
        'trait_distribution': trait_dist[:10],
        'trait_percentages': trait_pct[:10],
        'positive_negative': pos_neg,
        'negative_trait_count': negative_trait_count,
        'daily_trend': daily_trend,
        'trait_trend': trait_trend,
        'total_count': len(rows)
    }
