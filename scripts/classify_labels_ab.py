# -*- coding: utf-8 -*-
"""
A/B 라벨 분류기
================
178개 마이크로 라벨을 '경량 분류기로 학습 가능(A)' vs '추론 전담(B)'으로
자동 분류한다. 판단 근거는 trait 구조 + 맥락 규칙 + 라벨 정의에서 추출한
'추론 난이도 신호(reasoning signal)'다.

목적: KOTE식 평면 분류기가 178개 중 몇 개를 안정적으로 먹을 수 있는지를
      수치로 확인한다.
"""
import json, os, re
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(p):
    with open(os.path.join(BASE, p), encoding="utf-8") as f:
        return json.load(f)

pos = load("dataset/ori/positive_micro_labels_enhanced.json")["micro_labels"]
neg = load("dataset/ori/negative_micro_labels_enhanced.json")["micro_labels"]
traits = load("data/traits/trait_definitions.json")["traits"]
ctx = load("data/engine/context_rules.json")
train = load("dataset/ori/training_data_all_labels.json")

labels = pos + neg

# ---- 구조 신호 집합 구성 ----
hard_forbidden, soft_forbidden = set(), set()
for t in traits:
    hard_forbidden.update(t.get("hard_forbidden", []))
    for s in t.get("soft_forbidden", []):
        soft_forbidden.add(s["label"])

# 맥락 규칙에서 명시적으로 promotion/demotion 되는 라벨 (= 같은 말도 맥락 따라 의미 변동)
context_sensitive = set()
fe = ctx["front_end_context"]["rules"]
for tag in ("crisis", "normal", "innovation"):
    for pr in fe[tag].get("required_promotions", []):
        context_sensitive.add(pr["micro_code"])
    for dm in fe[tag].get("optional_demotions", []):
        context_sensitive.add(dm["micro_code"])

# 미러(flip) 위험: 같은 macro 번호가 긍/부정 양쪽에 존재 → 맥락절 하나로 뒤집힘
def macro_num(lid):  # "M19-01" -> "19"
    m = re.match(r"[MN](\d+)-", lid)
    return m.group(1) if m else None

pos_nums = {macro_num(l["label_id"]) for l in pos}
neg_nums = {macro_num(l["label_id"]) for l in neg}
mirror_nums = pos_nums & neg_nums

# 은닉 의도/화용 키워드 (표면 어휘로 안 드러나는 라벨)
INTENT_KW = ["조작","과장","은폐","가로채","독점","묵인","회피","위장","암시","유도",
             "가식","전가","숭배","차별","편파","강요","방치","독단","과시","왜곡",
             "기만","착취","억압","협박","압박","눈치","방조","책임 전가","공로"]

# 학습 데이터 라벨별 샘플 수
sample_count = Counter(d["label_id"] for d in train)

def variance(cw):
    vs = list(cw.values())
    return round(max(vs) - min(vs), 3)

rows = []
for l in labels:
    lid = l["label_id"]
    is_neg = lid.startswith("N")
    signals, score = [], 0

    if is_neg:
        score += 2; signals.append("부정라벨(역접·부정 처리)")
    if lid in context_sensitive:
        score += 2; signals.append("맥락 promotion/demotion")
    if lid in hard_forbidden:
        score += 1; signals.append("trait hard_forbidden(무효화)")
    if lid in soft_forbidden:
        score += 1; signals.append("trait soft_forbidden(패널티)")
    if macro_num(lid) in mirror_nums:
        score += 2; signals.append("긍/부정 미러(맥락 뒤집힘)")
    text = l["label_name"] + " " + l.get("definition","")
    if any(k in text for k in INTENT_KW):
        score += 2; signals.append("은닉 의도/화용")
    v = variance(l.get("context_weight", {"x":1}))
    if v >= 0.4:
        score += 1; signals.append(f"맥락 가중치 편차 {v}")

    bucket = "A" if score <= 1 else ("C" if score <= 3 else "B")
    rows.append({
        "label_id": lid, "name": l["label_name"], "type": "neg" if is_neg else "pos",
        "score": score, "bucket": bucket, "samples": sample_count.get(lid, 0),
        "signals": "; ".join(signals) if signals else "—",
    })

rows.sort(key=lambda r: (r["bucket"], -r["score"], r["label_id"]))

# ---- 요약 ----
by_bucket = Counter(r["bucket"] for r in rows)
pos_b = Counter(r["bucket"] for r in rows if r["type"] == "pos")
neg_b = Counter(r["bucket"] for r in rows if r["type"] == "neg")

print("="*60)
print(f"총 라벨: {len(rows)}개  (pos {len(pos)} / neg {len(neg)})")
print("="*60)
print(f"{'버킷':<4}{'설명':<28}{'전체':>5}{'긍정':>6}{'부정':>6}")
desc = {"A":"분류기 적합(easy)","C":"분류기+규칙 보정","B":"추론 전담(hard)"}
for b in ("A","C","B"):
    print(f"{b:<4}{desc[b]:<24}{by_bucket.get(b,0):>5}{pos_b.get(b,0):>6}{neg_b.get(b,0):>6}")
print("-"*60)
cls = by_bucket.get("A",0) + by_bucket.get("C",0)
print(f"분류기 활용 가능(A+C): {cls}/{len(rows)}  ({cls*100//len(rows)}%)")
print(f"순수 추론 필요(B):     {by_bucket.get('B',0)}/{len(rows)}  ({by_bucket.get('B',0)*100//len(rows)}%)")

# ---- 마크다운 리포트 저장 ----
out = ["# A/B 라벨 분류 리포트", "",
       f"> 자동 생성 · 총 {len(rows)}개 라벨 · 기준: 추론 난이도 신호 점수", "",
       "## 요약", "",
       "| 버킷 | 의미 | 전체 | 긍정 | 부정 |",
       "|------|------|------|------|------|"]
for b in ("A","C","B"):
    out.append(f"| **{b}** | {desc[b]} | {by_bucket.get(b,0)} | {pos_b.get(b,0)} | {neg_b.get(b,0)} |")
out += ["", f"- 분류기 활용 가능(A+C): **{cls}/{len(rows)} ({cls*100//len(rows)}%)**",
        f"- 순수 추론 필요(B): **{by_bucket.get('B',0)}/{len(rows)} ({by_bucket.get('B',0)*100//len(rows)}%)**",
        "", "## 점수 기준", "",
        "| 신호 | 점수 | 의미 |",
        "|------|------|------|",
        "| 부정라벨 | +2 | 역접·부정 형태소 처리 필요 |",
        "| 맥락 promotion/demotion | +2 | 같은 말도 맥락 따라 의미 변동 |",
        "| 긍/부정 미러 | +2 | 맥락절 하나로 긍↔부 뒤집힘 (M19↔N19형) |",
        "| 은닉 의도/화용 | +2 | 표면 어휘로 안 드러남(조작·은폐·가로채기 등) |",
        "| hard_forbidden | +1 | trait 무효화 → 고정밀 요구 |",
        "| soft_forbidden | +1 | trait 패널티 |",
        "| 맥락 가중치 편차 ≥0.4 | +1 | 상황 의존 큼 |",
        "", "버킷: A(0~1) / C(2~3) / B(≥4)", "",
        "## 라벨별 분류", "",
        "| 라벨 | 이름 | type | 점수 | 버킷 | 근거 |",
        "|------|------|------|------|------|------|"]
for r in rows:
    out.append(f"| {r['label_id']} | {r['name']} | {r['type']} | {r['score']} | {r['bucket']} | {r['signals']} |")

with open(os.path.join(BASE, "docs/label_ab_classification.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n리포트 저장: docs/label_ab_classification.md")
