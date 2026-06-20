#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 1: 데이터 정합성 검증 스크립트
- C1: positive_micro_labels.json definition 필드 완성 여부
- C2: context_rules.json T14 중복 키 여부
- C3: negative_mapping_rules.json T10, T11 매핑 존재 여부
- 추가: 부정 레이블 definition 필드 완성 여부
- 추가: 과거시제 제외 문구 적용 여부 샘플 확인
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
errors = []
warnings = []

print("=" * 60)
print("데이터 정합성 검증 시작")
print("=" * 60)

# ── C1: positive_micro_labels.json definition 누락 체크 ──
print("\n[C1] positive_micro_labels.json definition 필드 확인...")
with open(ROOT / "data/micro_labels/positive_micro_labels.json", encoding="utf-8") as f:
    pos_data = json.load(f)

missing_def = []
for label in pos_data["micro_labels"]:
    if not label.get("definition"):
        missing_def.append(label["label_id"])

if missing_def:
    errors.append(f"[C1] definition 누락 레이블: {missing_def}")
    print(f"  [FAIL] 누락: {missing_def}")
else:
    print(f"  [OK] 전체 {len(pos_data['micro_labels'])}개 레이블 definition 완비")

# ── C2: context_rules.json 중복 키 체크 ──
print("\n[C2] context_rules.json T14 중복 키 확인...")
raw = open(ROOT / "data/engine/context_rules.json", encoding="utf-8").read()
keys = re.findall(r'"(T\d+)"\s*:', raw)
dups = {k for k in keys if keys.count(k) > 1}
if dups:
    errors.append(f"[C2] context_rules.json 중복 키: {dups}")
    print(f"  [FAIL] 중복 키 발견: {dups}")
else:
    print("  [OK] 중복 키 없음")

# ── C3: negative_mapping_rules.json T10, T11 매핑 확인 ──
print("\n[C3] negative_mapping_rules.json T10, T11 매핑 확인...")
with open(ROOT / "data/engine/negative_mapping_rules.json", encoding="utf-8") as f:
    nmr = json.load(f)
mapped_ids = {r["trait_id"] for r in nmr.get("trait_negative_rules", [])}
for tid in ["T10", "T11"]:
    if tid not in mapped_ids:
        errors.append(f"[C3] {tid} 매핑 없음")
        print(f"  [FAIL] {tid} 매핑 누락")
    else:
        print(f"  [OK] {tid} 매핑 존재")

# ── 추가: negative_micro_labels.json definition 확인 ──
print("\n[추가] negative_micro_labels.json definition 필드 확인...")
with open(ROOT / "data/micro_labels/negative_micro_labels.json", encoding="utf-8") as f:
    neg_data = json.load(f)

neg_missing = [l["label_id"] for l in neg_data["micro_labels"] if not l.get("definition")]
if neg_missing:
    warnings.append(f"[추가] 부정 레이블 definition 누락: {neg_missing}")
    print(f"  [WARN]  누락: {neg_missing}")
else:
    print(f"  [OK] 전체 {len(neg_data['micro_labels'])}개 부정 레이블 definition 완비")

# ── 추가: 과거시제 제외 문구 적용 샘플 확인 ──
PAST_SUFFIX = "과거 회상 서술"
print(f"\n[추가] 긍정 레이블 과거시제 제외 문구 적용 확인 (샘플 5개)...")
missing_past = [l["label_id"] for l in pos_data["micro_labels"]
                if PAST_SUFFIX not in l.get("not_when", "")]
if missing_past:
    warnings.append(f"[추가] 과거시제 제외 문구 미적용: {len(missing_past)}개")
    print(f"  [WARN]  미적용: {len(missing_past)}개 — {missing_past[:5]}")
else:
    print(f"  [OK] 전체 {len(pos_data['micro_labels'])}개 레이블 과거시제 제외 문구 적용됨")

# ── 결과 요약 ──
print("\n" + "=" * 60)
if errors:
    print(f"[FAIL] 검증 실패: {len(errors)}개 오류")
    for e in errors:
        print(f"  {e}")
else:
    print("[OK] 모든 CRITICAL 검증 통과")

if warnings:
    print(f"[WARN]  경고: {len(warnings)}개")
    for w in warnings:
        print(f"  {w}")

print("=" * 60)
sys.exit(1 if errors else 0)
