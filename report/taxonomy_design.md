# Taxonomy 설계 스펙 — 확장 가능 + 정밀 trait 호출

> 작성 2026-06-20 · 전제: **닫힌 데이터가 아니다.** micro 라벨·trait은 계속 추가된다.
> 목표: 많은 micro 라벨로 **올바른 trait 하나(또는 의도된 소수)**를 정밀 호출.
> 근거 데이터: `docs/taxonomy_audit.md`(라벨 정리), `docs/trait_overlap_audit.md`(과호출 구조).

---

## 0. 두 줄 요약

- 현재 과호출(한 입력에 여러 trait 점화)의 원인은 모델이 아니라 **구조**다 — trait 5개(T01·T06·T08·T10·T11)가 **고유 앵커 없이 공유 hub 라벨로만** 구성돼 항상 이웃과 같이 켜진다.
- 해법 = trait마다 **고유 앵커(discriminative micro)** 부여. 이것이 곧 "**micro를 더 추가해 trait을 제대로 부른다**"는 확장 방향과 동일하다.

---

## 1. 핵심 개념: 라벨의 3가지 역할

micro 라벨을 trait 호출 기여도로 3분류한다. (신규 추가 시 반드시 명시)

| 역할 | 정의 | fan-out | trait 호출 가중치 |
|------|------|---------|------------------|
| **anchor** | 그 trait에만 있는 **고유 필수** 라벨. trait의 정체성. | 1 | 高 (단독으로 trait 점화 견인) |
| **discriminative** | 소수(1~2) trait에만 등장, 변별력 있음 | 1~2 | 中 |
| **supporting (hub)** | 여러 trait에 공유되는 일반 행동 | ≥3 | 低 (보강만, 단독 점화 불가) |

**원칙: 정밀도는 anchor에서 나온다. hub는 점수를 거들 뿐 trait을 단독으로 켜지 못한다.**

---

## 2. 정밀 호출 규칙 (over-firing 차단)

trait 점수 = Σ(라벨 가중치 × 역할계수). 역할계수: anchor 1.0 / discriminative 0.6 / supporting 0.3 (초안값, 튜닝 대상).

호출 게이트:
1. **anchor 필수 게이트**: trait이 켜지려면 그 trait의 anchor가 **최소 1개** 탐지돼야 한다. → 공유 hub만으로는 절대 점화 안 됨 (현재 과호출의 직접 차단).
2. **상대 우위**: 여러 trait이 임계를 넘으면, anchor 점유가 높은 trait 우선.
3. 예외: 의도적으로 함께 호출돼야 하는 trait(예: 복합 리더십)은 화이트리스트로 명시.

> 현재 엔진은 required(AND) 충족으로 trait을 켠다. 여기에 **"required 중 1개 이상은 anchor여야"**를 추가하면 구조만으로 과호출이 크게 줄어든다.

---

## 3. 확장 규칙 (append-only)

### 3-1. ID 정책
- micro `M##-##`/`N##-##`, trait `T##`/`T1##` 는 **append-only**. 한 번 부여한 번호는 **재사용·재번호 금지**.
- 폐기는 삭제가 아니라 `"deprecated": true` + `"superseded_by": "<id>"` 표시. → 과거 학습데이터·결과와 호환 유지.

### 3-2. micro 라벨 추가 체크리스트
- [ ] `label_id`(신규 번호), `label_name`, `macro`, `definition`, `when`, `not_when`, `context_weight`
- [ ] `role`: anchor | discriminative | supporting **명시**
- [ ] 소속 trait의 `required`/`optional`에 연결 (안 하면 **orphan** = 결과에 안 쓰임)
- [ ] 기존 라벨과 의미 중복 점검 (→ 중복이면 추가 대신 기존 강화)

### 3-3. trait 추가 체크리스트
- [ ] `trait_id`(신규), `trait_name`, `description`, `trait_type`
- [ ] **anchor ≥ 1** (없으면 반려 — 정밀 호출 불가)
- [ ] `required`/`optional`/`hard_forbidden`/`soft_forbidden`/`context_weight`/`k_trait`
- [ ] 기존 trait과 시그니처 Jaccard 점검 (≥0.5면 중복 → 신설 대신 기존 분화/병합 고려)

### 3-4. 추가 후 자동 검증 (회귀)
추가 시마다 두 감사 스크립트를 재실행해 회귀를 막는다:
- `scripts/trait_overlap_audit.py` → 앵커 없는 trait / 고중첩 쌍 0 유지 확인
- `scripts/taxonomy_audit.py` → 신규 라벨이 orphan 아닌지, 과세분 안 만드는지 확인

---

## 4. 현재 상태 진단 (정리 대상)

### 4-1. 앵커 없는 trait 5개 → 앵커 부여 필요
`T01, T06, T08, T10, T11`. 각각 고유 필수 라벨이 0개. **orphan을 앵커로 승격**해 해결 가능.

| 앵커 없는 trait | 앵커 후보 (orphan/저fan-out에서) |
|---|---|
| T06 Execution Driver | M40-01 예외관리(능동), M44-02 성취지향 |
| T10 Strategic Execution | M27-01 전략적 자원배분(현 공유) → 고유화, M41-02 균형적 정보처리 |
| T01 Strategic Decisive | M06-01 세부 실행지침 계열 고유화 |
| T08 Emotional Intelligence | M29-01 팀 웰빙 케어, M38-01 경청·공감 소통 |
| T11 Empathetic | M42-01 직원 중심성, M14 계열 정리 후 |

*(후보는 데이터 혼동 기반 힌트 — 최종 배치는 도메인 판단)*

### 4-2. 중복 trait 쌍 → 병합 또는 분화 결정
| 쌍 | Jaccard | 결정 필요 |
|---|---|---|
| T06 ↔ T10 | 0.67 | 병합? 아니면 각자 앵커로 분화? |
| T08 ↔ T11 | 0.50 | 병합? 분화? |
| T01 ↔ T10 | 0.44 | 실행계열 3개(T01/T06/T10) 재정의 |
| T02 ↔ T11 | 0.38 | 공감계열 경계 정리 |

### 4-3. orphan 48개 → 앵커 승격 / 신규 trait / 폐기
- 고F1 부정 확장군 **N38~N43**(방임·학대·부패·나르시시즘 등): trait 미연결. → 부정 trait(T101~T106) 편입 또는 신규 risk trait 신설.
- 긍정 확장군 **M36~M47**: 일부는 앵커 후보(4-1), 일부는 기존과 중복 → 정리.

### 4-4. 과세분 macro 병합/계층화
`N08(책임전가 계열), L14(타인우선), L15(심리적안전 6개)` — 내부혼동 높음. 병합 또는 2단(macro→micro) 분류.

---

## 5. 진행 순서 (정리 → 확장)

1. **[도메인 결정 필요]** 4-2 중복 trait: 병합 vs 분화 방향 확정.
2. 4-1 앵커 부여: 각 앵커없는 trait에 고유 anchor 연결(orphan 승격 우선).
3. 4-3 orphan 처리: 편입/신설/폐기 일괄.
4. 4-4 과세분 병합/계층화.
5. `role` 필드·`deprecated` 필드를 스키마에 도입, 2개 감사 스크립트를 회귀 게이트로 상시화.
6. 정리된 taxonomy 위에서 → hard 평가셋 → 모델 bake-off (이전 합의 순서).

> 이 문서는 살아있는 스펙이다. 라벨/trait 추가 시 4·5장을 갱신한다.
