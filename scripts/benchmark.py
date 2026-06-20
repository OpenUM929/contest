#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 4: 개선 전/후 벡터 검색 성능 비교
- Recall@5: 상위 5개 결과 안에 기대 레이블 포함 여부
- Top-1 정확도: 1위 결과가 기대 레이블인지 여부
- 사용법: python scripts/benchmark.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

TEST_CASES = [
    # (입력 텍스트, 기대 레이블 ID, 설명)
    ("문제가 발생하여 즉시 결단을 내렸다. 빠르게 결론을 내릴 것이다.",
     "M19-01", "T04 위기 결단"),

    ("약속했지만 실제로는 지키지 않았다. 사실은 처음부터 그럴 의도가 없었다.",
     "N30-01", "T105 약속 불이행"),

    ("데이터를 의도적으로 수정했다. 사실과 다른 내용을 보고했다.",
     "N34-01", "T103 데이터 조작"),

    ("의견을 충분히 들은 후 신속하게 결정했다.",
     "M19-01", "M19 vs N19 경계(긍정)"),

    ("혼자서 바로 결정해버렸다. 팀 의견은 전혀 듣지 않았다.",
     "N19-01", "M19 vs N19 경계(부정)"),

    ("팀원의 성과를 본인 성과로 발표했다.",
     "N09-01", "공로 독점"),

    ("팀의 미래 방향과 목표를 명확히 제시했다.",
     "M01-01", "비전 제시"),

    ("실수해도 괜찮아요, 제가 책임집니다. 팀원을 외부 압박으로부터 보호하겠습니다.",
     "M15-06", "심리적 보호"),

    ("충분한 준비 없이 급작스럽게 변화를 지시했다. 구성원 교육도 없이 강행했다.",
     "N05-02", "준비 없는 변화"),

    ("인력·시스템·예산을 갖추고 나서 혁신 프로젝트를 추진했다.",
     "M05-02", "준비된 변화 실행"),
]


def run_benchmark():
    print("=" * 60)
    print("벡터 검색 성능 벤치마크")
    print("=" * 60)

    try:
        from src.vector_search import VectorSearcher
        searcher = VectorSearcher()
    except Exception as e:
        print(f"[FAIL] VectorSearcher 초기화 실패: {e}")
        print("  힌트: python build_vector_db.py 를 먼저 실행하세요")
        sys.exit(1)

    total = len(TEST_CASES)
    top1_hits = 0
    recall5_hits = 0

    print(f"\n{'번호':<4} {'설명':<22} {'기대':<10} {'1위':<10} {'R@5':<6} {'결과'}")
    print("-" * 70)

    for i, (text, expected, desc) in enumerate(TEST_CASES, 1):
        results = searcher.search(text, k=5, expand=True)
        top_ids = [r['label_id'] for r in results]
        top1 = top_ids[0] if top_ids else "-"
        in_top1 = top1 == expected
        in_top5 = expected in top_ids

        top1_hits += int(in_top1)
        recall5_hits += int(in_top5)

        status = "[OK]" if in_top1 else ("[WARN]" if in_top5 else "[FAIL]")
        conf = f"{results[0]['confidence']:.3f}" if results else "N/A"
        print(f"{i:<4} {desc:<22} {expected:<10} {top1:<10} {'✓' if in_top5 else '✗':<6} {status} ({conf})")

    print("-" * 70)
    print(f"\n결과 요약:")
    print(f"  Top-1 정확도: {top1_hits}/{total} = {top1_hits/total*100:.1f}%")
    print(f"  Recall@5:     {recall5_hits}/{total} = {recall5_hits/total*100:.1f}%")
    print(f"\n목표: Top-1 ≥ 70%, Recall@5 ≥ 90%")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
