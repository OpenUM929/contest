# -*- coding: utf-8 -*-
"""
Taxonomy v4 빌드 — 합당성 결함 수정 + 앵커 부여 (1항 구현)
=========================================================
v3를 로드해 changeset을 적용, v4 새 파일을 생성(append-only, v3 보존).
근거/판정: docs/taxonomy_validity_review.md

적용:
  1) 중복 micro 7건 병합 → deprecated + superseded_by, trait 참조는 생존 라벨로 치환
  2) 무앵커 trait 5개에 고유 앵커(fan-out=1) 부여
  3) 부정 아키타입·긍정 orphan → 매칭 trait optional 매핑 (de-orphan)
  4) M41-02 macro 오타 "M41"→"L41"
  5) 각 trait에 anchor 필드, 각 micro에 role 필드 신설
자체 검증: 무앵커 trait=0, 잔여 orphan 수 출력.
"""
import json, os, re
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(BASE, *a)
def load(p):
    with open(P(p), encoding="utf-8") as f:
        return json.load(f)

tdef = load("data/traits/trait_definitions.json")
posj = load("dataset/ori/positive_micro_labels_enhanced.json")
negj = load("dataset/ori/negative_micro_labels_enhanced.json")
train = load("dataset/ori/training_data_all_labels.json")
has_samples = {r["label_id"] for r in train}

# ---------------- changeset ----------------
DEPRECATE = {  # 폐기 -> 생존
    "M09-01": "M08-02", "M12-03": "M15-01", "M18-02": "M34-01",
    "M26-01": "M22-02", "M31-01": "M28-02", "M41-01": "M32-01", "N14-02": "N09-01",
}
ANCHOR_ADD = {  # trait -> required 앵커로 추가
    "T01": "M36-01", "T06": "M44-02", "T08": "M32-01", "T10": "M27-01", "T11": "M29-01",
}
# 앵커를 고유(fan-out=1)로 만들기 위해 제거할 곳: 라벨 -> [(trait, list)]
ANCHOR_REMOVE = {
    "M32-01": [("T13", "optional")],
    "M27-01": [("T06", "optional"), ("T10", "optional")],
}
OPT_ADD = {  # trait -> optional 로 추가 (de-orphan)
    # 부정 아키타입
    "T101": ["N38-01", "N38-02"],
    "T102": ["N38-03", "N42-01", "N25-01", "N03-04"],
    "T103": ["N40-01", "N40-02", "N41-01", "N43-01", "N16-01", "N05-04"],
    "T104": ["N39-01", "N39-02", "N39-03"],
    "T106": ["N39-04", "N41-02", "N41-03", "N13-01", "N06-03"],
    # 긍정 orphan (확신 높은 것)
    "T09": ["M36-03", "M36-04", "M43-03", "M16-01"],
    "T07": ["M39-01"],
    "T06": ["M40-01", "M40-02", "M46-01", "M24-02", "M27-02"],
    "T05": ["M41-02"],
    "T11": ["M42-01", "M25-01", "M48-01"],
    "T02": ["M43-01", "M47-01", "M47-02"],
    "T03": ["M46-02", "M36-02"],
    "T13": ["M45-01", "M45-02"],
    "T14": ["M22-03", "M13-01"],
    "T12": ["M43-02"],
}

def sub(l):  # deprecated 참조 치환
    return DEPRECATE.get(l, l)

traits = tdef["traits"]
tmap = {t["trait_id"]: t for t in traits}

# 1) deprecated 참조 치환 (모든 리스트)
for t in traits:
    for k in ("required", "optional", "hard_forbidden"):
        t[k] = list(dict.fromkeys(sub(l) for l in t.get(k, [])))
    for s in t.get("soft_forbidden", []):
        s["label"] = sub(s["label"])

# 2) 앵커 제거(고유화) → 추가
for lab, locs in ANCHOR_REMOVE.items():
    for tid, key in locs:
        if lab in tmap[tid].get(key, []):
            tmap[tid][key] = [x for x in tmap[tid][key] if x != lab]
for tid, lab in ANCHOR_ADD.items():
    req = tmap[tid].setdefault("required", [])
    if lab not in req:
        req.append(lab)
    # required로 올라간 라벨이 optional에 있으면 제거
    tmap[tid]["optional"] = [x for x in tmap[tid].get("optional", []) if x != lab]

# 3) optional 매핑 (de-orphan)
for tid, labs in OPT_ADD.items():
    opt = tmap[tid].setdefault("optional", [])
    req = tmap[tid].get("required", [])
    for l in labs:
        if l not in opt and l not in req:
            opt.append(l)

# 4) fan-out 계산 → anchor 필드
fan = defaultdict(set)
for t in traits:
    for l in set(t.get("required", [])) | set(t.get("optional", [])):
        fan[l].add(t["trait_id"])
for t in traits:
    t["anchor"] = [l for l in t.get("required", []) if len(fan[l]) == 1]

# 5) micro 파일: role/deprecated/macro 수정
def role_of(lid):
    if lid in DEPRECATE: return "deprecated"
    f = len(fan.get(lid, ()))
    if f == 0: return "orphan"
    if any(lid in t["anchor"] for t in traits): return "anchor"
    return "supporting" if f >= 3 else "discriminative"

for arr in (posj["micro_labels"], negj["micro_labels"]):
    for m in arr:
        lid = m["label_id"]
        if lid == "M41-02" and m.get("macro") == "M41":
            m["macro"] = "L41"                       # 4) 오타 수정
        m["role"] = role_of(lid)
        if lid in DEPRECATE:
            m["deprecated"] = True
            m["superseded_by"] = DEPRECATE[lid]

# ---------------- write ----------------
tdef["schema_version"] = "2026-06-v4"
tdef["trait_library_version"] = "v4.0"
tdef["changeset_ref"] = "docs/taxonomy_validity_review.md"
posj["schema_version"] = negj["schema_version"] = "2026-06-v4"
json.dump(tdef, open(P("data/traits/trait_definitions_v4.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
json.dump(posj, open(P("dataset/ori/positive_micro_labels_v4.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
json.dump(negj, open(P("dataset/ori/negative_micro_labels_v4.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# ---------------- 자체 검증 ----------------
defines = set()
for t in traits:
    defines |= set(t.get("required", [])) | set(t.get("optional", []))
pos_traits = [t for t in traits if t["trait_type"] == "positive"]
no_anchor = [t["trait_id"] for t in pos_traits if (set(t["required"]) | set(t["optional"])) and not t["anchor"]]
all_micro = {m["label_id"] for m in posj["micro_labels"] + negj["micro_labels"]}
orphan_after = sorted(l for l in all_micro
                      if l in has_samples and l not in defines and l not in DEPRECATE)

print("=== Taxonomy v4 빌드 완료 ===")
print(f"중복 병합(deprecated): {len(DEPRECATE)}건")
print(f"무앵커 trait(목표 0): {no_anchor if no_anchor else '0 ✅'}")
print("앵커 부여 결과:")
for tid in ("T01", "T06", "T08", "T10", "T11"):
    print(f"  {tid}: anchor={tmap[tid]['anchor']}")
print(f"잔여 orphan(매핑 안 된 micro): {len(orphan_after)}개")
if orphan_after:
    print(f"  {', '.join(orphan_after)}")
print("\n출력: data/traits/trait_definitions_v4.json, dataset/ori/{positive,negative}_micro_labels_v4.json")

# changelog
cl = ["# Taxonomy v4 변경 로그", "",
      f"> v3→v4 자동 빌드 (`scripts/build_taxonomy_v4.py`). 근거: `docs/taxonomy_validity_review.md`", "",
      "## 1. 중복 병합 (deprecated)"]
for d, s in DEPRECATE.items():
    cl.append(f"- {d} → **{s}** (deprecated, superseded_by)")
cl += ["", "## 2. 앵커 부여 (무앵커 trait 해소)"]
for tid in ("T01", "T06", "T08", "T10", "T11"):
    cl.append(f"- {tid} {tmap[tid]['trait_name']}: anchor = {tmap[tid]['anchor']}")
cl += ["", f"## 3. de-orphan", f"- 매핑 후 잔여 orphan: {len(orphan_after)}개 ({', '.join(orphan_after) if orphan_after else '없음'})",
       "", "## 4. 기타", "- M41-02 macro 'M41'→'L41' 오타 수정", "- 전 micro에 `role`(anchor/discriminative/supporting/orphan/deprecated) 부여",
       "- 전 trait에 `anchor` 필드 부여"]
open(P("docs/taxonomy_v4_changelog.md"), "w", encoding="utf-8").write("\n".join(cl))
print("changelog: docs/taxonomy_v4_changelog.md")
