# Taxonomy 확장 워크플로 (평가 데이터 유입 대비)

> 2026-06-20 · 평가 데이터(다면평가 실문장)가 들어오면 micro 라벨·trait이 늘어난다.
> 이 문서는 **"새 라벨을 어떻게 안전하게 추가하는가"**를 절차 + 자동 게이트로 고정한다.
> 핵심 원칙: **append-only**(삭제 금지, deprecated+superseded_by), **모든 추가는 `scripts/validate_taxonomy.py` 통과 필수**.

---

## 0. 단일 진실원
- `src/taxonomy.py` — 라벨/trait 로드 + canon(deprecated→생존) 맵 + 불변식 점검을 **한 곳**에서 제공.
  과거 eval_hard/bakeoff/build 에 복붙돼 있던 canon 로직을 여기로 일원화함. 신규 스크립트는 반드시 여기서 import.
- 데이터 파일(append-only): `data/traits/trait_definitions_v4.json`,
  `dataset/ori/{positive,negative}_micro_labels_v4.json`.

## 1. 불변식(회귀 게이트) — `scripts/validate_taxonomy.py`
라벨/trait을 추가·수정할 때마다 실행. 위반 시 종료코드 1 → 머지 금지.

| 코드 | 불변식 | 왜 |
|---|---|---|
| I1 anchor | 모든 trait은 required 안의 *살아있는* 앵커 ≥1 | 공유 hub 단독 점화(과호출) 차단 |
| I2 orphan | 학습데이터 있는 라벨은 어떤 trait에든 연결 | 분류돼도 trait 집계 안 되는 사각 제거 |
| I3 deprecated | superseded_by 는 살아있는 라벨을 가리킴(체인 해소) | canon 정규화 무결성 |
| I4 ref | trait 참조 라벨 실존 + deprecated 직접참조 금지 | 끊긴 참조/유령 라벨 방지 |
| I5 dup | label_id 중복 정의 금지 | ID 충돌 방지 |
| I6 dupname | 살아있는 라벨끼리 동일 label_name 금지 | 과세분/복제 조기 탐지 |

현재 상태(2026-06-20): **micros=178, traits=20, deprecated=7, orphans=0, 6/6 통과.**

## 2. 새 micro 라벨 추가 절차
1. **ID 부여**: 기존 macro 군이면 `M<NN>-<nn>` 다음 번호. 새 행동군이면 새 macro. **절대 기존 ID 재사용·삭제 금지.**
2. **필드**: `label_id, label_name, macro, weight, definition, when, not_when, context_weight, role`.
   - 긍정 라벨 `not_when` 에는 과거시제 제외 문구 포함(기존 관례).
3. **역할(role) 자동판정** — `Taxonomy.suggested_role(id)` (fan-out 기준):
   - fan-out 1 → **anchor 후보** (그 trait 고유 변별 라벨)
   - fan-out 2~3 → **discriminative**
   - fan-out 4+ → **supporting (hub)** — hub는 required로 쓰지 말 것(과호출 유발)
4. **trait 연결**: 최소 한 trait의 `required`(핵심) 또는 `optional`(보강)에 등재 → I2(orphan) 회피.
5. **과세분 방지(granularity 규칙)**: 새 라벨이 기존 라벨과 (a)동일 macro + (b)when 예시가 70%+ 겹치면 **별도 라벨 대신 기존 라벨 강화**. 위반 시 L14/L15/N08 식 과세분 재발 → I6/과호출 audit으로 잡힘.
6. `validate_taxonomy.py` 통과 확인.

## 3. 새 trait 추가 절차
1. `trait_id` 부여(긍정 T##, 부정 T1##). append-only.
2. **anchor 필수**: 그 trait 고유의 required 라벨 ≥1을 `anchor` 에 명시. 없으면 → 먼저 discriminative micro를 만들어 앵커로. (I1이 강제)
3. `required/optional/hard_forbidden/soft_forbidden/context_weight/k_trait` 채움.
4. 인접 trait과 Jaccard 중첩 점검(`scripts/trait_overlap_audit.py`) — J≥0.3이면 사실상 중복 의심, 앵커로 변별 강화.
5. `validate_taxonomy.py` + `trait_overlap_audit.py` 통과.

## 4. 라벨 폐기(병합) 절차
- 삭제하지 않는다. 해당 라벨에 `"deprecated": true, "role": "deprecated", "superseded_by": "<생존ID>"` 추가.
- 모든 비교/학습은 `Taxonomy.canon()` 으로 생존 라벨에 정규화 → 과거 데이터 호환 유지.

## 5. 상시 게이트(권장 실행 순서)
```
python -X utf8 scripts/validate_taxonomy.py     # 불변식 (필수 통과)
python -X utf8 scripts/trait_overlap_audit.py   # 구조적 과호출 점검
python -X utf8 scripts/taxonomy_audit.py        # confusion/orphan 상세
```

---

## 6. 남은 도메인 결정(데이터 와도 유효, 의미 변경이라 사람이 판단)
- **required-hub 7개 강등**: `M10-01·M19-01·M01-01·M11-01·M10-02·M12-01·M14-01` 이 아직 여러 trait의 required 공유 → 각 trait에 앵커가 생긴 지금은 이들을 required→optional로 내리면 과호출 추가 감소. 단 trait 의미가 바뀌므로 도메인 확인 후 적용.
- **N15-07/N24-02, M38-01/M38-02 귀속(2026-06-20 적용)**: 잔여 orphan 4개를 형제 라벨 보유 trait에 optional로 연결(N15-07·N24-02→T102 Authoritarian, M38-01·M38-02→T11 Empathetic). 평가 데이터에서 더 적합한 trait이 보이면 재배치 가능.
