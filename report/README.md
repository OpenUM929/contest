# 📂 report — 리더십 진단 근거 자료실

이 폴더에는 우리 리더십 진단의 **모든 근거·분석 문서**가 모여 있습니다.

## 어디부터 볼까요?
| 독자 | 시작 문서 |
|---|---|
| **처음·비전문가** | 👉 [**WHITEPAPER.md**](WHITEPAPER.md) — "왜 믿어도 되는가"를 비유로 |
| 유형별 근거를 보고 싶다 | [INDEX.md](INDEX.md) — 구성개념별 trait↔micro·출처 카드 |
| 주장을 직접 검증하고 싶다 | [FACT_CHECK.md](FACT_CHECK.md) — 링크·인용구·체크박스 |
| 자료가 얼마나 단단한지 | [MATERIALS_ASSESSMENT.md](MATERIALS_ASSESSMENT.md) — 보수적 자기평가 |
| **평가 데이터셋을 만든다** | ⭐ [GOLD_LABELING_PROTOCOL.md](GOLD_LABELING_PROTOCOL.md) — 골드 라벨링 작업 표준서(κ·누수방지·층화) |

## 구성
- **근거 보고서**: WHITEPAPER · INDEX · FACT_CHECK · CAUSAL_REPORT · MATERIALS_ASSESSMENT · SOURCE_RIGOR_PLAN · CODEBOOK · yukl_coverage · IMPROVEMENT_PLAN
- **유형별 카드**: [`constructs/`](constructs/) (구성개념 21개)
- **분석·설계 문서**: taxonomy_academic_review · evidence_tracking · algorithm_models · taxonomy_extension_workflow · taxonomy_design · taxonomy_validity_review · taxonomy_v4_changelog · taxonomy_audit · trait_overlap_audit · hard_eval_bakeoff · ai_feasibility_study 등

## 자동 생성 주의
`INDEX.md`, `FACT_CHECK.md`, `constructs/*.md`는 `scripts/gen_evidence_docs.py`가 생성합니다(직접 수정 금지). 원천 데이터는 `data/evidence/`(레지스트리·인과·척도맵). 갱신: 데이터 수정 → 생성기 재실행.

> 데이터 원천(`data/evidence/`)과 생성 스크립트(`scripts/`)는 이동하지 않았습니다 — 이 폴더는 *읽는 산출물*만 모읍니다.
