# Plan 문서 정리 및 이관 — 계획서 문서 통합

> 상태: DN | 작성일: 2026-06-10 | 완료일: 2026-06-10
> 작업 유형: 문서 정리/이관 (root → plan 통합)

---

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| 2026-06-10 | 전체 | 최초 작성 |

---

## 1. 개요

root/ 및 doc/에 분산된 계획서 문서를 `plan/` 디렉토리로 통합 정리한다.
제거 대상 파일의 참조를 모두 갱신한 후 원본을 삭제한다.

---

## 2. 작업 목록

### Phase 1: root/ → plan/ 이관

| # | 원본 경로 | 대상 경로 |
|---|-----------|-----------|
| 1 | `이음_구현계획_개요.md` | `plan/reference/이음_구현계획_개요.md` |
| 2 | `이음_구현계획_A_공공데이터.md` | `plan/reference/pipeline-A/plan_A_public-data.md` |
| 3 | `이음_구현계획_B_사용자대화.md` | `plan/reference/pipeline-B/plan_B_user-chat.md` |
| 4 | `이음_구현계획_C_감정분석.md` | `plan/reference/pipeline-C/plan_C_emotion-analysis.md` |
| 5 | `이음_구현계획_D_수필생성.md` | `plan/reference/pipeline-D/plan_D_essay-generation.md` |
| 6 | `이음_구현계획_E_안전감지.md` | `plan/reference/pipeline-E/plan_E_safety-detection.md` |
| 7 | `이음_구현계획_F_복지사.md` | `plan/reference/pipeline-F/plan_F_welfare-worker.md` |
| 8 | `이음_구현계획_G_보안.md` | `plan/reference/pipeline-G/plan_G_security.md` |
| 9 | `이음_시나리오테스트.md` | `plan/reference/이음_시나리오테스트.md` |
| 10 | `이음_재검증보고서_전체.md` | `plan/reference/이음_재검증보고서_전체.md` |
| 11 | `이음_간단사용가이드.md` | `plan/reference/이음_간단사용가이드.md` |

### Phase 2: doc/ → plan/ 이관

| # | 원본 경로 (doc/) | 대상 경로 (plan/) |
|---|------------------|-------------------|
| 12 | `이음_구현계획_A_주제선정_복지사중심.md` | `plan/reference/pipeline-A/plan_A-prime_welfare-topic.md` |
| 13 | `이음_설문지통합관리_구현계획_20260602.md` | `plan/reference/pipeline-A/plan_A-dblprime_survey-integration.md` |
| 14 | `이음_프롬프트_안개비재설계_리포트.md` | `plan/reference/pipeline-A/이음_프롬프트_안개비재설계_리포트.md` |
| 15 | `주제발행_4단계_지문.md` | `plan/reference/pipeline-A/주제발행_4단계_지문.md` |

### Phase 3: 참조 경로 갱신

| # | 파일 | 갱신 내용 |
|---|------|-----------|
| 16 | `plan/이음_통합구현계획_20260604.md` §6 | root/doc 참조 → plan/reference 경로 |
| 17 | `.clinerules/docs/project/README.md` 파이프라인 목록 | root 경로 → plan/reference 경로 |
| 18 | `.clinerules/core/00-core.md` 작업 분류표 (L21-27) + 핵심 규칙 (L67,69) | root 경로 → plan/reference 경로 |

### Phase 4: 원본 제거

| # | 대상 |
|---|------|
| 19 | root/ 이음_구현계획_*.md 파일 11개 삭제 |
| 20 | root/ 이음_시나리오테스트.md, 이음_재검증보고서_전체.md, 이음_간단사용가이드.md 삭제 |
| 21 | doc/ 디렉토리 전체 삭제 |

---

## 3. 영향도

- **Phase 3 구현 진행 중** → 문서만 이동, 코드 미변경
- **참조 경로 갱신 누락 시 Broken Link** → Phase 3에서 전수 점검
- **Rollback**: git restore로 원복 가능

---

## 4. 완료 조건

- [ ] 모든 계획서 문서가 `plan/reference/` 아래에 존재
- [ ] 3개 참조 파일의 경로가 갱신됨
- [ ] root/ 및 doc/ 원본 제거 완료
- [ ] `git status` 확인, 불필요 파일 미포함
