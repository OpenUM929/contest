# -*- coding: utf-8 -*-
"""v3 vs v4 과호출 구조 before/after 검증."""
import json, os
from collections import defaultdict
from itertools import combinations
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def L(p): return json.load(open(os.path.join(BASE, p), encoding="utf-8"))["traits"]

def metrics(traits):
    sig, req = {}, {}
    for t in traits:
        sig[t["trait_id"]] = set(t.get("required", [])) | set(t.get("optional", []))
        req[t["trait_id"]] = set(t.get("required", []))
    fan = defaultdict(set)
    for tid in sig:
        for m in sig[tid]: fan[m].add(tid)
    pos = [t for t in traits if t["trait_type"] == "positive"]
    no_anchor = [t["trait_id"] for t in pos
                 if sig[t["trait_id"]] and not [m for m in req[t["trait_id"]] if len(fan[m]) == 1]]
    hi_jac = 0
    for a, b in combinations(sig, 2):
        if sig[a] & sig[b]:
            j = len(sig[a] & sig[b]) / len(sig[a] | sig[b])
            if j >= 0.3: hi_jac += 1
    req_shared = sum(1 for m in fan if len([t for t in traits if m in req[t["trait_id"]]]) >= 2)
    return no_anchor, hi_jac, req_shared

for tag, path in [("v3", "data/traits/trait_definitions.json"),
                  ("v4", "data/traits/trait_definitions_v4.json")]:
    na, hj, rs = metrics(L(path))
    print(f"[{tag}] 무앵커 trait: {len(na)}{na if na else ''} | 고중첩쌍(J≥0.3): {hj} | required공유 라벨: {rs}")
