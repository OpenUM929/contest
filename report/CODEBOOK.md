# 매핑 코드북 (M10) — 구성개념→Trait→Micro 코딩 프로토콜

> 2026-06-20 · 목적: 매핑이 *단일 평정자(나)의 즉흥 판단*이 아니라 **재현가능한 규칙**임을 문서화. 2차 독립 코딩으로 평정자간 일치(κ)를 측정해 편향을 제거하기 위한 기준.

## 1. 코딩 단위
- **L0 구성개념**: 검증된 리더십 이론/척도(예: 변혁적, 서번트, Schmidt TLS).
- **L1 trait**: 우리 22개 trait. `trait_kind` = style/capability/context/risk.
- **L2 micro**: 우리 180개 행동 라벨.

## 2. 코딩 규칙 (구성개념 → trait)
**R-A1**: trait↔구성개념 링크는 trait이 구성개념의 *검증된 정의 차원(facet)* 중 ≥1개를 구현할 때만. 차원 출처는 `scale_item_map.json`/`causal_rationale.json`에 명시.
**R-A2**: 한 trait이 복수 구성개념에 연결 가능(같은 행동이 두 이론의 차원을 만족할 때). 단 각 링크는 독립적으로 R-A1 충족.
**R-A3**: `trait_kind=capability/context`인 trait은 구성개념 부모를 요구하지 않음(by-design). style/risk만 부모 필수(`coverage_audit.py`).
**R-A4**: 증분변량이 변혁적 대비 미미(contested/redundant)하면 별도 trait 신설 금지 → 흡수(parsimony).
**R-A5**: 'X특화'(green 등)는 trait 아닌 context로 흡수.

## 3. 코딩 규칙 (trait → micro)
**R-B1**: micro↔trait 링크는 micro의 `definition`/`when`이 그 trait이 구현하는 차원의 *관찰가능 행동*일 때.
**R-B2**: 각 trait은 fan-out=1의 고유 **앵커** micro ≥1 보유(`validate_taxonomy` I1).
**R-B3**: 역할 자동판정 — fan-out 1=anchor, 2~3=discriminative, 4+=supporting(hub). hub은 required로 쓰지 않음(과호출 방지).
**R-B4**: 검증 척도가 있으면 micro를 그 척도 facet에 대응(`scale_item_map.json`, M7).

## 4. 인과 강도 표기 (필수 필드)
각 trait_link: `causal_grade`(이론연역/수렴근거/논쟁) + `rival`(경쟁 설명) + `disconfirm`(반증 조건). (`causal_rationale.json`)

## 5. 출처 규칙
**R-C1**: 2차 경로(blog/researchgate/academia/studocu) 금지(`validate_evidence` E2).
**R-C2**: 정량 주장은 `claim_quote`(+가능시 페이지) 보유.
**R-C3**: 핵심 구성개념은 독립 출처 ≥2(삼각검증) + 최근 5년 출처 ≥1 권장(`source_rigor_audit` R1/R2).
**R-C4**: 메타 출처는 강도 메타데이터(`n_studies`/`effect_size`/`journal_tier`).

## 6. 2차 독립 코딩 절차 (편향 제거)
1. 본 코드북만 주고 **독립 코더**(외부 전문가 또는 별도 에이전트)가 구성개념→trait, trait→micro를 *블라인드* 재코딩.
2. 우리 매핑과 대조해 **Cohen's κ** 산출(아래 템플릿).
3. κ<0.6 항목은 불일치 → 토론·정의 명료화 후 재코딩.

### κ 기록 템플릿
| 매핑 항목 | 코더1(우리) | 코더2(독립) | 일치 |
|---|---|---|---|
| T09←transformational:IM | ✓ | ? | ? |
| … | | | |
> κ = (Po − Pe)/(1 − Pe). 목표 κ≥0.7(상당 일치).

## 7. 신규 추가 시 체크리스트
- [ ] 구성개념 차원 출처(peer-reviewed, DOI)
- [ ] R-A1~A5 충족(부모·수준·중복·도메인)
- [ ] 앵커 micro(R-B2) + 척도 대응(R-B4)
- [ ] causal_grade+rival+disconfirm
- [ ] 독립 출처 ≥2 + claim_quote
- [ ] `validate_taxonomy`·`validate_evidence`·`coverage_audit`·`source_rigor_audit` 통과

> 한계: 현재 1차 코딩=본 프로젝트. **2차 독립 코딩(κ)은 외부 코더 필요** — 미실시(정직 표기). 실시 전까지 매핑은 '규칙기반 단일코딩'.
