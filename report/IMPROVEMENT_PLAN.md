# 근거 품질 개선 계획 (조사 기반) — 데이터 없이 올릴 수 있는 4개 차원

> 2026-06-20 · 대상: `MATERIALS_ASSESSMENT.md`에서 **조사/재설계로 개선 가능**한 4개 차원.
> 제외: 실증층(다면평가 데이터 필요 → 별도) · 문서화층(이미 4.5).
> 원칙: 각 작업은 **측정가능한 합격기준(Definition of Done)** 과 **목표 점수**를 가진다. 모든 변경은 append-only + `validate_taxonomy.py` 게이트 통과.

| 차원 | 현재 | 목표 | 상한(데이터 없이) | 병목 |
|---|---|---|---|---|
| 출처 품질 | 3.0 | **4.2** | 4.5 | 2차 링크·DOI 미통일·FACT_CHECK 미검증 |
| 학술 근거 연결 | 3.5 | **4.5** | 4.5 | 사후 매핑·근거 없는 trait |
| 인과 논증 | 3.5 | **4.3** | 4.5 | 반증 구조 부재·L1→L2 약함 |
| 구성 타당도 | 2.5 | **3.5** | 3.5* | 수준혼재·중복·무근거 trait (*요인분석=데이터 필요라 3.5에서 캡) |

> 종합 기대: ~3.0 → **~3.8 / 5** (실증층 1.5 고정 가정). 실증 착수 시 추가 상승.

---

## Phase 1 — 출처 품질 정제 (가장 싸고, 나머지를 떠받침) → 3.0→4.2
**왜 먼저**: 근거·인과·타당도 모두 *출처*를 인용하므로, 출처가 1차·검증가능해야 윗단이 단단해진다.

### 작업
1. **출처 스키마 강화**: 레지스트리/causal의 각 source에 `doi`, `journal`, `peer_reviewed`(bool), `evidence_grade`(M=메타분석 / S=체계적종설 / E=1차실증 / R=리뷰 / B=서적·기타) 필드 추가.
2. **2차 경로 제거**: researchgate/academia.edu/블로그 링크 → 원저널 DOI로 교체. 교체 불가 시 `evidence_grade=B`로 강등 표기.
3. **정량 주장 출처고정**: 각 수치(예: 서번트 +12%, ρ=.34, Schmidt 5차원)에 **원문 위치(페이지/표)+직접 인용구**를 `claim_quote`로 기록 → 검증 가능.
4. **FACT_CHECK 사람검증 준비·실행**: 사용자가 링크 열어 대조할 수 있게 행마다 인용구 노출. (사용자가 "내가 확인" → 확인 결과를 `verified:true/날짜`로 반영.)
5. **게이트화**: `validate_evidence.py`(신규) — 모든 source에 doi 또는 grade=B, 모든 정량주장에 claim_quote 존재를 검사. 미충족 시 실패.

### 합격기준(DoD) — **Phase1 완료 2026-06-20**
- [x] 2차 경로 링크 **0건** (leadershipahoy 블로그·researchgate → Antonakis 2003·Paulhus & Williams 2002·Schmidt ProQuest로 교체)
- [x] peer_reviewed 비율 **92%**(B 제외), 핵심 수치에 claim_quote 부착(서번트·Schmidt α·Wang ρ 등)
- [ ] FACT_CHECK 사람검증 완료율 100% — **사용자 작업**(링크·인용구·체크박스 준비됨)
- [x] `validate_evidence.py` 통과 (E1~E4 OK)

> 산출: `scripts/upgrade_sources.py`·`fix_sources.py`·`validate_evidence.py`. 출처 스키마에 evidence_grade/peer_reviewed/doi/claim_quote 추가.

---

## Phase 2 — 학술 근거 연결: 사후매핑 → 이론선행 재도출 → 3.5→4.5
**왜**: 현재는 "라벨을 이론에 끼워맞춤". 모든 trait이 *검증된 구성개념의 정의 차원*을 부모로 갖도록 뒤집는다.

### 작업
1. **차원 출처(provenance) 의무화**: 각 trait에 `dimensional_parent`(예: T09←"Inspirational Motivation@transformational") 필드. 부모 없는 trait 금지.
2. **커버리지 매트릭스**: Yukl 12행동(clarifying…scanning) × FRLM 차원 × 우리 trait → 매핑/누락/중복 표 자동생성(`coverage_audit.py`). 누락(external/empowering/recognizing)·중복(T01/T06/T10) 가시화.
3. **추가 문헌 조사**(WebSearch): 미해결 구성개념의 *측정도구 차원* 확정 — Servant(Liden 7차원 vs SL-7), Empowering(Ahearne/Amundsen 척도 차원), Abusive Supervision(Tepper 15문항 차원), Identity(ILI 4차원). 각 차원을 우리 micro에 매핑.
4. **무근거 trait 처리 결정문**: T12 Balanced(구성개념 없음)→재정의(ambidextrous 근거 조사) 또는 deprecate, 근거 메모로 기록.

### 합격기준 — **완료 2026-06-20 (전체 진행 지시)**
- [x] `dimensional_parent` 보유 — **style/risk 100%(19/19)**. capability/context(T04·T05·T08)는 by-design 제외. `coverage_audit.py` trait_kind 인식형.
- [x] Yukl 12행동 커버리지 매트릭스 — `yukl_coverage.md`, 10/12(83%) 커버, 갭=recognizing·scanning(external)
- [x] T12 처리 — **ambidextrous(Rosing 2011)로 재정의·구제**(폐기 대신 학술 부모 부여)
- [~] 고중첩쌍(T01/T06/T10) — Initiating Structure 공유부모로 *가시화*, 실제 통합은 요인분석(데이터) 보류

> 산출: `scripts/coverage_audit.py`·`phase23_build.py`. 신규 1차 출처: 참여적(AMJ 2017)·행동적진실성(Simons 2002)·학대적감독(Tepper 2000).

---

## Phase 3 — 인과 논증: 정당화 → 반증가능 구조 → 3.5→4.3
**왜**: 현재 인과는 *지지 근거*만. 학술적 인과는 *반증 조건*과 *경쟁가설*을 동반해야 강해진다.

### 작업
1. **인과 링크 3종 세트 의무화**: causal의 각 trait_link/micro에 `support`(지지근거) + `rival`(경쟁 설명) + `disconfirm`(무엇이 관찰되면 이 인과가 틀린가). 예) "M19-01 신속판단→T01" 의 rival="N19-01 독단과 표면유사", disconfirm="독단 맥락에서 빈출 시 인과 무효".
2. **L1→L2 보강**: micro를 *행동 마커 문헌*에 연결 가능한 것은 외부 근거 부착(예: 경청·공감 micro ↔ Consideration 행동 마커). 불가하면 "내부 정의 기반(중신뢰)"로 등급 명시.
3. **변별(discriminant) 근거**: 인접 trait 쌍(T07↔T11, T01↔T06)마다 "왜 다른가"의 경계조건+중복 메타 인용.
4. **인과 등급표**: 각 링크에 `causal_grade`(이론연역 / 수렴근거 / 논쟁) 부여 → CAUSAL_REPORT에 자동 반영.

### 합격기준 — **완료 2026-06-20**
- [x] mapped 구성개념의 trait_link에 support+rival+disconfirm 부착(19 구성개념, `phase23_build.py`)
- [x] 인접 trait 변별: rival에 표면유사 trait 명시(T101↔임파워링, T102↔T01 등)
- [x] 인과 등급(`causal_grade`: 이론연역/수렴근거/논쟁) 부착, 구성개념 문서 §3 렌더링

> "논쟁" 등급(T06 보상·T13 진성/윤리·T04 위기·T14 디지털)은 watch backlog와 일치.

---

## Phase 4 — 구성 타당도: 개념·구조 정리(데이터 전 가능분) → 2.5→3.5
**왜**: 요인분석(수렴/변별 타당도)은 데이터가 필요하지만, **내용 타당도·구조 정리는 조사로 지금 가능**. 그래서 상한 3.5.

### 작업 (v5 재설계 — 개념적·비데이터)
1. **수준 혼재 정리**: T05 Analytical·T08 EI → *역량(capability) 레이어*로 재분류(peer trait 아님). T04 Crisis·green → *context 차원*으로 흡수. (엔진은 context 이미 보유.)
2. **중복 통합**: T01/T06/T10 과업축 → 의미기준 2개로 통합 또는 앵커 변별 강화. T13(진성·윤리) → 변혁축 흡수 결정(Phase2 근거 기반).
3. **신설(근거 충족분)**: Servant 정식화(T07·T11 통합), Empowering 신설 + 신규 micro(위임·자율부여, Phase2 척도 차원에서 도출), Abusive Supervision 신설(N15 분리).
4. **커버리지·중복 게이트 상시화**: `trait_overlap_audit`(J)·`coverage_audit`를 회귀 게이트에 편입.

### 합격기준 — **대부분 완료 2026-06-20**
- [x] 수준 혼재 정리 — `trait_kind`(style/capability/context/risk) 전 trait 부여. T05·T08=capability, T04=context로 명시 분리
- [x] 무근거 trait 0 — T12=ambidextrous로 구제(폐기 안 함)
- [x] Empowering(**T15**, 신규 micro M49-01/02)·Abusive Supervision(**T107**, 신규 N40-01) 신설 + validate_taxonomy 통과. Servant는 T07·T11로 실현(구성개념 문서화)
- [x] Yukl 커버리지 83%(≥80%)
- [~] 고중첩쌍(T01/T06/T10 J≥0.5) **0** — 미달성. 공유부모 가시화까지만, 실제 통합·deprecate는 **요인분석(데이터) 필요**로 보류(이번 비파괴 범위 밖)

> 산출: `build_v5.py`(trait_kind·T15·T107·신규micro), `build_v5_evidence.py`(initiating_structure·ambidextrous 부모, empowering→T15·abusive→T107 인과). v5: 22 trait·180 micro.

> 한계 명시: 위를 다 해도 **수렴·변별 타당도(요인분석)는 데이터 없이는 불가** → 3.5에서 캡. 데이터 유입 시 Phase 5(실증)로 4.5+ 목표.

---

## 순서·의존성·산출물
```
Phase1(출처) ──┬─→ Phase2(근거 재도출) ──┬─→ Phase4(구성 정리)
               └─→ Phase3(인과 반증)  ───┘
```
- **Phase1 선행**(다른 단계가 출처를 인용). Phase2·3 병렬 가능. Phase4는 2·3 결과에 의존.
- 산출물: 스키마 확장(레지스트리/causal/trait) · 신규 게이트 `validate_evidence.py`·`coverage_audit.py` · 갱신 문서(전 evidence 문서 재생성) · 결정문(T12·T13·통합) · v5 taxonomy.
- 역할: **조사·문서·게이트=나** / **FACT_CHECK 검증·통합·deprecate 도메인 결정=사용자**.

## 추적
- 각 Phase 합격기준을 체크리스트로 관리, 완료 시 `MATERIALS_ASSESSMENT.md` 점수 재산정.
- 모든 변경은 `evidence_trends.py`/`validate_taxonomy.py` 신호와 정합 유지.
