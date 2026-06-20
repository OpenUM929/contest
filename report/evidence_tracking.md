# 학술 근거 추세 추적 & 갱신 프로세스

> 2026-06-20 · 문제의식(사용자): *학술 근거는 계속 쌓인다. 그러니 trait/리더십 결과가 시대에 따라 어떻게 변하는지 '추세'를 추적하고, 매번 전수 재조사 없이 갱신할 수 있어야 한다.*
> 해법: 구성개념별 **증거 레지스트리 + 추세 모델 + 주기적 재검토 루프**.

---

## 1. 왜 '추세'를 분리해서 보나
리더십 구성개념의 학술적 위상은 두 축이 따로 움직인다:
- **validity_status** — 실증적으로 얼마나 견고/구별되는가 (emerging→growing→established / contested→redundant→declining→superseded)
- **attention_trend** — 최근 학술 관심·출판이 느는가 (rising / stable / declining)

**둘의 괴리가 핵심 신호다.** 예) *진성 리더십*: 관심은 rising인데 validity는 contested(변혁적과 중복). 관심만 보면 trait을 추가하고 싶지만, 타당도를 보면 흡수해야 한다. 이 괴리를 자동으로 잡는 게 갱신의 1순위.

## 2. 구성요소
| 파일 | 역할 |
|---|---|
| `data/evidence/leadership_evidence_registry.json` | 구성개념별 위상·추세·증분변량·출처(연도)·매핑 trait·`implication`·`last_reviewed` |
| `scripts/evidence_trends.py` | 추세 스냅샷 + 4가지 갱신 신호 + 재검토 기한 경보 출력 |
| 본 문서 | 추세 모델 정의 + 갱신 루프 절차 |

## 3. `implication`(taxonomy 조치) 코드
`keep`(유지) · `add`(신설/보강) · `merge`(통합) · `split`(분리) · `deprecate`(폐기) · `watch`(관찰) · `out_of_scope`(분석수준 밖).
→ 레지스트리의 implication이 곧 taxonomy v(n+1)의 변경 backlog. validate_taxonomy 게이트와 append-only 원칙으로 반영([[taxonomy-extension-workflow]]).

## 4. 갱신 루프 (cadence: 6개월, 또는 주요 메타분석 출현 시 즉시)
```
1) 재검토 트리거: next_review_due 도래(evidence_trends.py가 경보) 또는 새 메타/SLR 인지
2) 문헌 재조사: 추천 검색어(아래) + KCI/RISS 국내 + 최신 메타·SLR 우선
3) 레지스트리 갱신: 각 construct의 validity_status·attention_trend·incremental_validity·sources·last_reviewed 수정. 신규 구성개념은 항목 추가
4) 신호 재계산: evidence_trends.py 실행 → [신호1 괴리][신호2 신설][신호3 통합/폐기][신호4 범위밖] 확인
5) taxonomy 반영: implication에 따라 trait add/merge/deprecate. validate_taxonomy.py 통과 필수
6) last_full_review·next_review_due 갱신
```

### 추천 검색어(국내외 병행)
- 영문: `<construct> leadership meta-analysis 2025`, `<construct> incremental validity beyond transformational`, `<construct> systematic literature review`, `leadership construct redundancy / proliferation`
- 국문(KCI/RISS): `변혁적/서번트/진성/공유/디지털/적응형 리더십`, `리더십 메타분석`, `리더십 효과 조직효과성`

## 5. 결과(leadership output)에 추세 반영
trait 결과를 사용자에게 보여줄 때, 매핑된 구성개념의 위상을 함께 노출 가능:
- `evidence_status`: 예) "T07/T11 → 서번트(growing↑, 변혁적 대비 증분 최대)" / "T13 → 진성·윤리(contested, 변혁적과 중복)"
- 이렇게 하면 **결과의 학술적 신뢰도와 시의성**이 드러나고, 위상이 바뀌면 결과 해석도 자동으로 따라 바뀐다.

## 6. 2026-06-20 스냅샷 요약 (구성개념 17개, 현재 backlog)
- **add(신설/보강)**: 서번트(긍정 신설 1순위, T07·T11 통합) · **임파워링(긍정 신설 1순위, 독립 메타근거; 부정 N24·N15-07의 긍정 대칭축)** · 학대적 감독(부정 신설 1순위) · 거래적 보상(긍정 보강)
- **merge**: 적응형 → change축(T14/T04) 흡수
- **watch(괴리·중복)**: 진성·윤리(T13 흡수 검토) · 디지털(Technological 축 분리 여부) · 정체성(장기, 탐지난이도) · **겸손·포용(서번트/관계축·심리안전과 인접 → 흡수 가능성)**
- **watch(도메인 렌즈)**: **녹색/환경 — 새 성향이 아니라 '환경특화 변혁적'이므로 trait이 아닌 context(sustainability)로 모델링 권고**(T04 Crisis와 동일 논리)
- **out_of_scope**: 공유/분산(팀 수준)
- **keep**: 변혁적(단 도메인 파생형 green/digital/sustainability 확장 추세) · 방임형 · 독성 · Dark Triad
- 다음 재검토: **2026-12-20**

### 이번 확장(2026-06-20)에서 얻은 두 가지 구조적 통찰
1. **임파워링**은 그냥 '추가'가 아니라 *비대칭 교정*: 현재 부정엔 과도통제(N24)·과잉보호(N15-07)가 있는데 긍정 대칭이 없었음. 독립 메타근거(Lee 2018 등)까지 있어 서번트와 동급 1순위.
2. **'X특화 리더십'(green/environmental, 그리고 일부 digital)은 새 trait이 아니라 도메인 적용**. → trait 축을 늘리는 대신 **context 차원(crisis/normal/innovation/…에 sustainability 추가)**으로 흡수하는 게 과증식을 막는 정답. 이 원칙을 확장 워크플로의 판정 규칙으로 채택.

> 상세 근거·출처는 `taxonomy_academic_review.md` §6~7, 위상 데이터는 레지스트리 JSON.
