# 🔴 00-Core Rules (항상 최우선 적용)

> ⚠️ **이 파일은 나침반이다. 구체적 내용은 다른 문서에 있다.**
> **작업 유형을 파악 → 아래 분류표에서 해당 유형 찾기 → 명시된 문서로 이동 → 그 문서 읽기**
> **추측 금지. 모르면 사용자에게 "어느 문서를 봐야 합니까?" 질문**

---

## 현재 프로젝트

**[.clinerules/docs/project/README.md](../docs/project/README.md)** - 이음(以音) 프로젝트 상세 구조 및 작업 유형 분류 참조

---

## 작업 유형 분류표

| 작업 유형 | 이동할 문서 |
|-----------|-------------|
| **🔴 계획서/기획서/설계서 작성 요청** | **[00-core/03.plan-mode.md](00-core/03.plan-mode.md) — 저장 위치·파일명 형식 반드시 확인** |
| **이음 프로젝트 전반** | **[.clinerules/docs/project/README.md](../docs/project/README.md)** |
| **파이프라인 A (공공데이터)** | **[plan/reference/pipeline-A/plan_A_public-data.md](../../plan/reference/pipeline-A/plan_A_public-data.md)** |
| **파이프라인 A' (복지사중심)** | **[plan/reference/pipeline-A/plan_A-prime_welfare-topic.md](../../plan/reference/pipeline-A/plan_A-prime_welfare-topic.md)** |
| **파이프라인 A'' (설문지통합)** | **[plan/reference/pipeline-A/plan_A-dblprime_survey-integration.md](../../plan/reference/pipeline-A/plan_A-dblprime_survey-integration.md)** |
| **파이프라인 B (사용자 대화)** | **[plan/reference/pipeline-B/plan_B_user-chat.md](../../plan/reference/pipeline-B/plan_B_user-chat.md)** |
| **파이프라인 C (감정 분석)** | **[plan/reference/pipeline-C/plan_C_emotion-analysis.md](../../plan/reference/pipeline-C/plan_C_emotion-analysis.md)** |
| **파이프라인 D (수필 생성)** | **[plan/reference/pipeline-D/plan_D_essay-generation.md](../../plan/reference/pipeline-D/plan_D_essay-generation.md)** |
| **파이프라인 E (안전 감지)** | **[plan/reference/pipeline-E/plan_E_safety-detection.md](../../plan/reference/pipeline-E/plan_E_safety-detection.md)** |
| **파이프라인 F (복지사)** | **[plan/reference/pipeline-F/plan_F_welfare-worker.md](../../plan/reference/pipeline-F/plan_F_welfare-worker.md)** |
| **파이프라인 G (보안)** | **[plan/reference/pipeline-G/plan_G_security.md](../../plan/reference/pipeline-G/plan_G_security.md)** |
| **시간 문제** | **[.clinerules/docs/development/time-handling-rules.md](../docs/development/time-handling-rules.md)** |
| **필드명/네이밍** | **[.clinerules/docs/development/field-naming-convention.md](../docs/development/field-naming-convention.md)** |
| 공통 UI/디자인 | [04.design-change.md](04.design-change.md) |
| 백엔드 API | [03.workflow.md](03.workflow.md) |
| 데이터베이스 / 테이블 / DDL | [.clinerules/docs/development/database-naming-standard.md](../docs/development/database-naming-standard.md) |
| 리팩토링 | [01.legacy-protection.md](01.legacy-protection.md) FIRST |
| 기능 문제 분석/디버깅 | [03.workflow.md](03.workflow.md) |
| Git 작업 | [06.git-rules.md](06.git-rules.md) |
| 공통 모듈 수정/추가 | Glob으로 실제 파일 경로 확인 후 상대 경로 계산 |
| 복구/롤백 | [07.recovery-rules.md](07.recovery-rules.md) |
| **지침 수정/추가/삭제** | **[08.guideline-modification.md](08.guideline-modification.md)** - 반드시 사용자 요청 시에만 |
| **프로젝트 분석/나침반 생성** | **[10.project-compass.md](10.project-compass.md)** |
| **성능 분석/최적화 계획** | **[11-performance-optimization-plan.md](11-performance-optimization-plan.md)** |
| **영향도 분석 보고서** | **[12-impact-analysis-report.md](12-impact-analysis-report.md)** |
| **요구사항 명확화** | **[13-requirements-clarification.md](13-requirements-clarification.md)** |
| **주석/로그 제거** | **[14.comment-log-removal.md](14.comment-log-removal.md)** |
| **운영자 메뉴얼 작성/수정** | **[.clinerules/docs/msys/operator-manual/DEVELOPMENT.md](../docs/msys/operator-manual/DEVELOPMENT.md)** |

---

## 핵심 규칙 문서 위치

| 규칙 | 문서 위치 |
|------|-----------|
| **이음 프로젝트** | **[.clinerules/docs/project/README.md](../docs/project/README.md)** - 프로젝트 나침반 |
| 전역 잠금 규칙 | [00-core/01.global-rules.md](00-core/01.global-rules.md) |
| Legacy Protection | [01.legacy-protection.md](01.legacy-protection.md) |
| 문서 가이드 | [02.documentation.md](02.documentation.md) |
| 워크플로우 | [03.workflow.md](03.workflow.md) |
| UI/디자인 변경 | [04.design-change.md](04.design-change.md) |
| 테스트 | [05.testing.md](05.testing.md) |
| Git 작업 | [06.git-rules.md](06.git-rules.md) |
| 복구/롤백 | [07.recovery-rules.md](07.recovery-rules.md) |
| **지침 추가/삭제/수정** | **[08.guideline-modification.md](08.guideline-modification.md)** |
| 질문 규칙 | [09.question-rules.md](09.question-rules.md) |
| Project Compass | [10.project-compass.md](10.project-compass.md) - 프로젝트 분석/나침반 |
| 성능 분석/최적화 계획 | [11-performance-optimization-plan.md](11-performance-optimization-plan.md) |
| 영향도 분석 보고서 | [12-impact-analysis-report.md](12-impact-analysis-report.md) |
| 요구사항 명확화 | [13-requirements-clarification.md](13-requirements-clarification.md) |
| 시나리오 테스트 | [plan/reference/이음_시나리오테스트.md](../../plan/reference/이음_시나리오테스트.md) |
| 재검증 보고서 | [plan/reference/이음_재검증보고서_전체.md](../../plan/reference/이음_재검증보고서_전체.md) |
| 통합 구현 계획 | [plan/이음_통합구현계획_20260604.md](../../plan/이음_통합구현계획_20260604.md) |
| 실행 트리거 | [00-core/02.triggers.md](00-core/02.triggers.md) |
| Plan Mode | [00-core/03.plan-mode.md](00-core/03.plan-mode.md) |
| 폴더 명칭 규칙 | [08-guideline-modification/04.folder-naming.md](08-guideline-modification/04.folder-naming.md) |
| 누락된 규칙 분석 및 새 지침 추가 절차 | [08-guideline-modification/06.missing-rules-analysis.md](08-guideline-modification/06.missing-rules-analysis.md) |

---

## 참조 검증 (반드시 적용)

- **다른 문서를 참조할 때마다 Glob으로 실제 존재 여부 확인**
- 존재하지 않는 문서 링크는 추가 금지
- 새 프로젝트 문서 생성 시 README.md 파일 필수
- 참조하는 문서가 없으면 사용자에게 "어떤 문서를 만들어야 하나?" 질문

---

항상 "현재 작업 유형이 무엇인가"를 스스로 판단하고, 해당 규칙 파일의 내용을 가장 강하게 반영해서 행동하라!
