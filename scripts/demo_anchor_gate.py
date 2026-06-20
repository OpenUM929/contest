# -*- coding: utf-8 -*-
"""앵커 게이트 효과 증명: 동일 v4 데이터에서 게이트 ON/OFF 점화 trait 수 비교."""
import sys, os, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.leadership_engine import LeadershipEngine

eng = LeadershipEngine(data_dir="./data")  # v4 (anchor 필드 포함)

def run(labels, gate):
    e = LeadershipEngine(data_dir="./data")
    if not gate:                              # 게이트 OFF = anchor 필드 제거 (v3 거동)
        for t in e.trait_definitions:
            t.pop('anchor', None)
    res = e.process([{"label_id": l, "confidence": 0.9} for l in labels])
    return res['trait_percentages_full']

cases = [
    ("공유 hub 단독 (M10-01 실행력)", ["M10-01"]),
    ("hub M19-01 + T06앵커 M44-02", ["M19-01", "M44-02"]),
    ("hub M01-01 + T01앵커 M36-01", ["M01-01", "M36-01"]),
    ("공감 hub M12-01 단독", ["M12-01"]),
]

print("=== 앵커 게이트 ON/OFF 점화 trait 비교 (v4 데이터) ===\n")
for desc, labels in cases:
    off = run(labels, gate=False)
    on = run(labels, gate=True)
    pos_off = [t['trait_id'] for t in off if t['type'] == 'positive']
    pos_on = [t['trait_id'] for t in on if t['type'] == 'positive']
    print(f"[{desc}]  입력 {labels}")
    print(f"  게이트 OFF: {len(pos_off)}개 점화 {pos_off}")
    print(f"  게이트 ON : {len(pos_on)}개 점화 {pos_on}")
    print()
