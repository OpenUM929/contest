# -*- coding: utf-8 -*-
"""
근거 자료 문서 자동 생성기.
입력: data/evidence/leadership_evidence_registry.json + taxonomy(v4 trait/micro)
출력: report/ 아래
  - INDEX.md                  : 전체 색인
  - FACT_CHECK.md             : 사실관계 확인용(주장 + 출처 링크 + 확인 체크박스)
  - constructs/<id>.md        : 리더십 유형별 trait↔micro 연계 + 근거 출처(각각)

자동 생성이므로 직접 수정 금지. 레지스트리/taxonomy 갱신 후 재실행.
실행: python -X utf8 scripts/gen_evidence_docs.py
"""
import json
import os
import sys
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))
from taxonomy import Taxonomy  # noqa: E402

REG = os.path.join(BASE, "data/evidence/leadership_evidence_registry.json")
OUT = os.path.join(BASE, "report")
CONS_DIR = os.path.join(OUT, "constructs")
os.makedirs(CONS_DIR, exist_ok=True)

with open(REG, encoding="utf-8") as f:
    reg = json.load(f)
CAUSAL_PATH = os.path.join(BASE, "data/evidence/causal_rationale.json")
causal = {}
if os.path.exists(CAUSAL_PATH):
    with open(CAUSAL_PATH, encoding="utf-8") as f:
        causal = json.load(f).get("constructs", {})
SCALE_PATH = os.path.join(BASE, "data/evidence/scale_item_map.json")
scale = {}
if os.path.exists(SCALE_PATH):
    with open(SCALE_PATH, encoding="utf-8") as f:
        scale = json.load(f).get("constructs", {})
tax = Taxonomy.load()
TODAY = date.today().isoformat()
ARROW = {"rising": "상승↑", "stable": "안정→", "declining": "하강↓"}
GEN_NOTE = ("> ⚙️ 자동 생성: `scripts/gen_evidence_docs.py` — **직접 수정 금지**. "
            "레지스트리/taxonomy 갱신 후 재실행.\n")


def micro_rows(trait_id):
    """trait의 required/optional micro를 (역할, id, 이름, micro_role) 행으로."""
    t = tax.traits.get(trait_id, {})
    rows = []
    for field in ("required", "optional"):
        for lid in t.get(field, []):
            m = tax.micros.get(lid, {})
            rows.append((field, lid, m.get("label_name", "?"), m.get("role", "-")))
    return rows


def write_construct(c):
    lines = [f"# {c['name_ko']}  (`{c['id']}`)", "", GEN_NOTE, ""]
    lines += [
        "## 1. 학술적 위상 (추세)", "",
        f"- **극성**: {c['polarity']}",
        f"- **타당도(validity)**: `{c['validity_status']}`",
        f"- **학술 관심(attention)**: {ARROW.get(c['attention_trend'], c['attention_trend'])}",
        f"- **최초 등장**: {c.get('first_seen_year','?')}",
        f"- **변혁적 대비 증분/효과**: {c.get('incremental_validity','-')}",
        f"- **taxonomy 조치(implication)**: `{c['implication']}`",
    ]
    if c.get("expected_outcomes"):
        lines.append(f"- **기대 outcome(노몰로지컬 네트워크)**: {c['expected_outcomes']}")
    if c.get("causal_evidence"):
        ce = c["causal_evidence"]
        lines.append(f"- **인과(construct→outcome)**: 메커니즘 {ce.get('mechanism','')} · 증거유형 `{ce.get('evidence_type','')}`")
    lines += [
        "", f"> {c['trend_note']}", "",
        "## 2. 연계된 Trait ↔ Micro Label", "",
    ]
    if c["mapped_traits"]:
        for tid in c["mapped_traits"]:
            t = tax.traits.get(tid)
            if not t:
                lines.append(f"### {tid} (정의 없음 — 확인 필요)\n")
                continue
            anc = ",".join(t.get("anchor", [])) or "-"
            lines.append(f"### {tid} · {t.get('trait_name','')}  (앵커: {anc})")
            lines.append("")
            lines.append("| 구분 | label_id | label_name | micro 역할 |")
            lines.append("|---|---|---|---|")
            for field, lid, name, role in micro_rows(tid):
                lines.append(f"| {field} | {lid} | {name} | {role} |")
            lines.append("")
    else:
        lines.append(f"**현재 연계 trait 없음** — 조치 `{c['implication']}`.  ")
        lines.append("→ 위 *학술적 위상*의 trend_note가 신설/흡수/범위판정 근거. "
                     "구현 시 이 구성개념을 어떤 trait·micro로 연결할지(또는 context로 흡수할지) 결정 필요.")
        lines.append("")

    # ── 측정도구 대응 (M7 척도-문항) ──
    sm = scale.get(c["id"])
    if sm:
        ref = sm.get("instrument_ref", {})
        doi = f" (doi:{ref['doi']})" if ref.get("doi") else ""
        lines += ["## 2b. 측정도구 대응 (검증된 척도 → 우리 micro)", "",
                  f"> 검증된 측정도구의 facet에 우리 micro를 대응 = '차원 라벨'을 넘어 *측정학적 조작화*로 정당화.",
                  "",
                  f"**측정도구**: {sm['instrument']} — {ref.get('cite','')}{doi}", "",
                  "| 척도 facet | trait | 대응 micro |", "|---|---|---|"]
        for fm in sm.get("facet_map", []):
            ms = ", ".join(fm.get("micros", []))
            lines.append(f"| {fm['facet']} | {fm.get('trait','')} | {ms} |")
        lines.append("")

    # ── 인과관계 근거 ──
    cz = causal.get(c["id"])
    lines += ["## 3. 인과관계 근거 (왜 이 trait인가 / 왜 이 micro인가)", ""]
    if cz and cz.get("trait_links"):
        if cz.get("dimensions"):
            src = cz.get("dimensions_source", {})
            srctxt = f" [출처]({src['url']})" if src.get("url") else ""
            lines.append(f"**구성개념 정의 차원**: {', '.join(cz['dimensions'])}.{srctxt}")
            lines.append("")
            lines.append("> (A) 구성개념의 *정의 차원*을 trait이 구현(instantiate)하고, "
                         "(B) 각 micro의 *행동 정의*가 그 차원의 관찰가능한 조작화다.")
            lines.append("")
        for tl in cz["trait_links"]:
            tid = tl["trait"]
            tname = tax.traits.get(tid, {}).get("trait_name", "")
            lines.append(f"### (A) {tid} {tname} ← {c['name_ko']}")
            lines.append(f"- **구현 차원**: {tl.get('instantiates','')}")
            lines.append(f"- **왜 이 trait인가(support)**: {tl.get('why','')}")
            if tl.get("causal_grade"):
                lines.append(f"- **인과 등급**: `{tl['causal_grade']}`")
            if tl.get("rival"):
                lines.append(f"- **경쟁 가설(rival)**: {tl['rival']}")
            if tl.get("disconfirm"):
                lines.append(f"- **반증 조건(disconfirm)**: {tl['disconfirm']}")
            lines.append("")
            lines.append(f"#### (B) {tid}의 핵심 micro 연관 근거")
            lines.append("| label_id | label_name | 행동 정의(근거) | 왜 이 trait의 micro인가 |")
            lines.append("|---|---|---|---|")
            for km in tl.get("key_micros", []):
                m = tax.micros.get(km["id"])
                if not m:
                    lines.append(f"| {km['id']} | (정의 없음·확인필요) | - | {km.get('why','')} |")
                    continue
                deff = (m.get("definition", "") or "").replace("|", "／")[:60]
                lines.append(f"| {km['id']} | {m.get('label_name','')} | {deff} | {km.get('why','')} |")
            lines.append("")
        lines.append("> 핵심 micro 외 나머지 required/optional의 trait↔micro 인과는 "
                     "각 라벨의 `definition`/`when`(§2 표의 라벨)이 1차 근거.")
        lines.append("")
    elif cz and cz.get("note"):
        lines.append(f"{cz['note']}")
        lines.append("")
    else:
        lines.append("_인과관계 근거 미작성 — `data/evidence/causal_rationale.json`에 추가 후 재생성._")
        lines.append("")

    lines += ["## 4. 근거 자료 (출처 — 직접 확인용 링크)", "",
              "> 등급 M=메타분석·S=체계적종설·E=1차실증·R=리뷰·B=기타. ✓=동료심사.", ""]
    for s in c["sources"]:
        grade = s.get("evidence_grade", "?")
        pr = "✓" if s.get("peer_reviewed") else "—"
        doi = f" · doi:{s['doi']}" if s.get("doi") else ""
        lines.append(f"- **[{grade}{pr}]** [{s['cite']} ({s['year']}, {s['type']})]({s['url']}){doi}")
        strength = " · ".join(filter(None, [
            f"k/N: {s['n_studies']}" if s.get("n_studies") else "",
            f"효과: {s['effect_size']}" if s.get("effect_size") else "",
            s.get("journal_tier", "")]))
        if strength:
            lines.append(f"  - 📊 {strength}")
        if s.get("claim_quote"):
            lines.append(f"  - 📌 *{s['claim_quote']}*")
    lines += ["", "---", f"_생성일 {TODAY} · last_reviewed {c['last_reviewed']}_", ""]

    path = os.path.join(CONS_DIR, f"{c['id']}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return os.path.relpath(path, OUT).replace("\\", "/")


def write_index(rel_paths):
    lines = [
        "# 근거 자료 색인 (리더십 유형별)", "", GEN_NOTE, "",
        "## 👉 처음이라면 여기부터: [**근거 백서 (WHITEPAPER)**](WHITEPAPER.md)",
        "> 초급자도 이해하도록 '왜 믿어도 되는가'를 이야기로 풀어쓴 대표 문서.",
        "",
        f"- 구성개념 {len(reg['constructs'])}개 · last_full_review {reg['last_full_review']} · "
        f"next_review_due {reg['next_review_due']}",
        "- 사실관계 확인: [FACT_CHECK.md](FACT_CHECK.md)",
        "- **인과관계 형성 리포트(왜 이렇게 형성됐나)**: [CAUSAL_REPORT.md](CAUSAL_REPORT.md)",
        "- 추세/신호 리포트: `python -X utf8 scripts/evidence_trends.py`",
        "- 레지스트리(원천): `data/evidence/leadership_evidence_registry.json`", "",
        "| 구성개념 | 극성 | 위상 | 관심 | 조치 | 연계 trait | 문서 |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in reg["constructs"]:
        traits = ",".join(c["mapped_traits"]) or "-"
        rel = rel_paths[c["id"]]
        lines.append(f"| {c['name_ko']} | {c['polarity'][:3]} | {c['validity_status']} | "
                     f"{ARROW.get(c['attention_trend'],'')} | `{c['implication']}` | {traits} | "
                     f"[보기]({rel}) |")
    with open(os.path.join(OUT, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_factcheck():
    lines = [
        "# 사실관계 확인 문서 (FACT CHECK)", "", GEN_NOTE, "",
        "> 목적: 각 주장(학술 근거)을 **출처 링크로 직접 검증**할 수 있게 정리. "
        "확인란에 체크하며 사실관계를 점검하세요. 자동 생성이므로 검증 결과는 "
        "레지스트리(trend_note/sources)에 반영 후 재생성합니다.", "",
        "| # | 구성개념 | 검증 대상 주장(인용구 우선) | 증분/효과 | 출처(등급·확인 링크) | 확인 |",
        "|---|---|---|---|---|---|",
    ]
    i = 1
    for c in reg["constructs"]:
        quote = next((s["claim_quote"] for s in c["sources"] if s.get("claim_quote")), None)
        claim = quote if quote else c["trend_note"].split(".")[0][:80]
        eff = (c.get("incremental_validity") or "-")[:40]
        srcs = " ; ".join(f"[{s.get('evidence_grade','?')}·{s['year']}]({s['url']})" for s in c["sources"])
        lines.append(f"| {i} | {c['name_ko']} | {claim} | {eff} | {srcs} | ☐ |")
        i += 1
    lines += [
        "", "## 확인 가이드", "",
        "1. 각 행의 출처 링크를 열어 주장(증분변량·차원·효과)이 실제 논문과 일치하는지 확인.",
        "2. 불일치/업데이트 발견 시: `data/evidence/leadership_evidence_registry.json`의 "
        "해당 construct를 수정(validity_status·attention_trend·incremental_validity·sources·last_reviewed).",
        "3. `python -X utf8 scripts/gen_evidence_docs.py` 재실행 → 본 문서·연계 문서 자동 갱신.",
        "4. `python -X utf8 scripts/evidence_trends.py`로 신호(괴리/신설/통합) 재확인.", "",
        f"_생성일 {TODAY}_", "",
    ]
    with open(os.path.join(OUT, "FACT_CHECK.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


rel_paths = {c["id"]: write_construct(c) for c in reg["constructs"]}
write_index(rel_paths)
write_factcheck()
print(f"생성 완료: {len(reg['constructs'])}개 construct 문서 + INDEX + FACT_CHECK → report/")
