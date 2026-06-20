#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
긍정 레이블 not_when 끝에 과거시제 제외 문구 일괄 추가
대상: positive_micro_labels.json + positive_micro_labels_enhanced.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
TARGETS = [
    ROOT / "data/micro_labels/positive_micro_labels.json",
    ROOT / "dataset/ori/positive_micro_labels_enhanced.json",
]
SUFFIX = "; 과거 회상 서술(~했었습니다, ~했었는데, 예전에~) 시 제외"

for path in TARGETS:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    changed = 0
    for label in data.get("micro_labels", []):
        nw = label.get("not_when", "")
        if SUFFIX not in nw:
            label["not_when"] = nw + SUFFIX
            changed += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[완료] {path.name}: {changed}개 레이블 수정")
