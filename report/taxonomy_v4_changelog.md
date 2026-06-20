# Taxonomy v4 변경 로그

> v3→v4 자동 빌드 (`scripts/build_taxonomy_v4.py`). 근거: `docs/taxonomy_validity_review.md`

## 1. 중복 병합 (deprecated)
- M09-01 → **M08-02** (deprecated, superseded_by)
- M12-03 → **M15-01** (deprecated, superseded_by)
- M18-02 → **M34-01** (deprecated, superseded_by)
- M26-01 → **M22-02** (deprecated, superseded_by)
- M31-01 → **M28-02** (deprecated, superseded_by)
- M41-01 → **M32-01** (deprecated, superseded_by)
- N14-02 → **N09-01** (deprecated, superseded_by)

## 2. 앵커 부여 (무앵커 trait 해소)
- T01 Strategic Decisive Leader: anchor = ['M36-01']
- T06 Execution Driver: anchor = ['M44-02']
- T08 Emotional Intelligence Leader: anchor = ['M32-01']
- T10 Strategic Execution Leader: anchor = ['M27-01']
- T11 Empathetic Leader: anchor = ['M29-01']

## 3. de-orphan
- 매핑 후 잔여 orphan: 5개 (M38-01, M38-02, M44-01, N15-07, N24-02)

## 4. 기타
- M41-02 macro 'M41'→'L41' 오타 수정
- 전 micro에 `role`(anchor/discriminative/supporting/orphan/deprecated) 부여
- 전 trait에 `anchor` 필드 부여