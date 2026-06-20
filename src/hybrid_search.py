#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
하이브리드 검색: Vector DB + LLM
- 1단계: Vector DB로 후보 15개 추출
- 1.5단계: 기계적 context 판단 (키워드 기반, 중립적)
- 2단계: LLM이 최종 라벨 선택 (부정/맥락 처리)
"""

import sys
import json
import os
from pathlib import Path


def detect_context_mechanical(text: str) -> str:
    """
    기계적 중립: 키워드 기반 context 판단
    LLM의 주관적 해석 배제, 객관적 키워드 매칭만 사용
    """
    crisis_keywords = [
        "문제", "발생", "긴급", "위기", "위급", 
        "갈등", "압력", "반대", "해고", "빠르게", "즉시"
    ]
    innovation_keywords = [
        "새로운", "혁신", "도전", "창의", "변화", 
        "창조", "실험", "아이디어"
    ]
    
    crisis_count = sum(1 for kw in crisis_keywords if kw in text)
    innovation_count = sum(1 for kw in innovation_keywords if kw in text)
    
    # 명확한 crisis 징후
    if "문제가 발생" in text or "긴급" in text or "위기" in text:
        return "crisis"
    if crisis_count >= 2:
        return "crisis"
    
    # 명확한 innovation 징후
    if innovation_count >= 2:
        return "innovation"
    
    # 기본값
    return "normal"

PROJECT_ROOT = Path(r"C:\dev\leadership")
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from vector_search import VectorSearcher
from nlp_pipeline import create_opencode_client, call_llm_with_retry, load_allowed_labels
from leadership_engine import LeadershipEngine

# 초기화
print("=" * 70)
print("하이브리드 시스템 초기화")
print("=" * 70)

searcher = VectorSearcher()
llm = create_opencode_client()
engine = LeadershipEngine(data_dir="./data")

# Label schema 로드
with open(PROJECT_ROOT / "data" / "labels" / "positive_labels.json", 'r', encoding='utf-8') as f:
    pos_schema = json.load(f)
with open(PROJECT_ROOT / "data" / "labels" / "negative_labels.json", 'r', encoding='utf-8') as f:
    neg_schema = json.load(f)

allowed_pos, _ = load_allowed_labels(pos_schema)
allowed_neg, _ = load_allowed_labels(neg_schema)
allowed_all = allowed_pos.union(allowed_neg)


def hybrid_extract(text: str, context: str = None, k=15) -> list:
    """하이브리드 추출 - 기계적 context 판단"""
    # 0.5단계: 기계적 context 판단 (LLM 주관성 배제)
    if context is None:
        context = detect_context_mechanical(text)
        print(f"  [기계적 판단] context = {context}")
    
    print(f"\n[1/3] Vector DB 검색 (Top-{k})...")
    vector_results = searcher.search(text, k=k, expand=True)
    
    # 후보 라벨 포맷팅
    candidates = []
    for r in vector_results:
        candidates.append(f"{r['label_id']}: {r['text'][:60]}")
    
    print(f"  후보 {len(candidates)}개 추출 완료")
    
    # 2단계: LLM 필터링 (context 정보 제공, 판단 요청 안 함)
    print(f"\n[2/3] LLM 분석 중 (context: {context})...")
    
    # 후보 라벨 텍스트 구성
    candidates_text = "\n".join(['- ' + c for c in candidates])
    
    prompt = f"""당신은 리더십 행동을 분석하여 관련 Micro Label을 선택하는 시스템입니다.

[입력 텍스트]
{text}

[맥락 정보 - 기계적 판단 결과]
Context: {context}

[후보 라벨 목록 (Vector DB 검색 결과 - 상위 {k}개)]
{candidates_text}

[분석 지침]
1. Negation 체크: "하지만", "실제로는", "안 함" 등 부정 표현이 있으면 해당 라벨 신뢰도 낮춤
2. 최종 라벨 선택: 후보 중 실제로 적용되는 라벨만 선택 (context 정보 참고)

[출력 형식 - 순수 JSON만]
{"selected_labels": [{"label_id": "M19-01", "confidence": 0.95, "reason": "빠르게 결론 → 신속 의사결정"}]}

[출력]
"""
    
    try:
        result = call_llm_with_retry(llm, prompt, allowed_all)
        print(f"  LLM 분석 완료")
        return result.get('selected_labels', []), context  # 기계적 판단 context 유지
    except Exception as e:
        print(f"  LLM 오류: {e}")
        # Fallback: Vector 결과 반환 (context 유지)
        return [{'label_id': r['label_id'], 'confidence': r['confidence']} for r in vector_results[:5]], context


def run_test_case(case_id, text, expected_primary, expected_labels, result_file):
    """테스트 케이스 실행 - 결과를 파일에 기록"""
    result_file.write("\n" + "=" * 70 + "\n")
    result_file.write(f"테스트: {case_id}\n")
    result_file.write("=" * 70 + "\n")
    result_file.write(f"입력: {text[:60]}...\n")
    
    # 하이브리드 추출
    labels, context = hybrid_extract(text)
    
    result_file.write(f"\n[3/3] Trait 추론 (context: {context})...\n")
    
    # LeadershipEngine용 데이터 변환
    micro_labels = []
    for l in labels:
        micro_labels.append({
            'label_id': l['label_id'],
            'confidence': l.get('confidence', 0.5),
            'context': context
        })
    
    # Trait 추론
    result = engine.process(micro_labels, context=context)
    
    primary = result.get('primary')
    secondary = result.get('secondary_details', [])
    
    # 결과 기록
    result_file.write("\n결과:\n")
    status = "PASS" if primary == expected_primary else "FAIL"
    result_file.write(f"  Primary Trait: {primary} (기대: {expected_primary}) [{status}]\n")
    result_file.write(f"  추출된 라벨: {sorted([l['label_id'] for l in labels])}\n")
    result_file.write(f"  기대 라벨: {sorted(expected_labels)}\n")
    
    return primary == expected_primary


if __name__ == "__main__":
    # 결과 파일 열기 (인코딩 문제 회피)
    with open(PROJECT_ROOT / "data" / "vectors" / "hybrid_test_results.txt", 'w', encoding='utf-8') as result_file:
        
        # T04-B 테스트
        t04_text = "문제가 발생했다. 지금 상황을 분석하고 있다. 빠르게 결론을 내릴 것이다. 모두 내 안내대로 행동해달라."
        t04_expected_primary = "T04"
        t04_expected_labels = {"M19-01", "M10-01", "M20-01", "M17-01"}
        
        result_t04 = run_test_case("T04-B", t04_text, t04_expected_primary, t04_expected_labels, result_file)
        
        # T105-A 테스트
        t105_text = "이번 quarter 성과 좋으면 즉시 승진시켜드립니다. 하지만 실제로는 그런 일 없습니다. 안 하면 해고하겠습니다."
        t105_expected_primary = "T105"
        t105_expected_labels = {"N02-01", "N02-02", "N02-03"}
        
        result_t105 = run_test_case("T105-A", t105_text, t105_expected_primary, t105_expected_labels, result_file)
        
        # 요약
        result_file.write("\n" + "=" * 70 + "\n")
        result_file.write("테스트 요약\n")
        result_file.write("=" * 70 + "\n")
        result_file.write(f"T04-B: {'PASS' if result_t04 else 'FAIL'}\n")
        result_file.write(f"T105-A: {'PASS' if result_t105 else 'FAIL'}\n")
    
    print("결과 저장 완료: data/vectors/hybrid_test_results.txt")
