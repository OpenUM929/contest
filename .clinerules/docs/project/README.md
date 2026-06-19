# 이음(以音) 프로젝트 나침반

## 프로젝트 개요

> 세대 간 소통과 정서적 연결을 위한 AI 기반 대화 서비스
> 노인과 청년을 연결하는 7개 파이프라인으로 구성

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | Python FastAPI, PostgreSQL, Redis |
| 프론트엔드 | React (Vite), TypeScript, Expo (React Native) |
| AI | Claude API, Whisper STT, TTS |
| 인프라 | Docker Compose |

---

## 프로젝트 구조

```
ium/
├── backend/          ← FastAPI 백엔드 (app/ 하위 라우터, 서비스, 모델)
│   ├── app/
│   │   ├── main.py         ← 앱 진입점
│   │   ├── routers/        ← API 라우터
│   │   ├── services/       ← 비즈니스 로직
│   │   ├── models/         ← DB 모델
│   │   └── utils/          ← 공통 유틸리티
│   ├── init.sql            ← 초기 DB 스키마
│   └── requirements.txt
├── dashboard/        ← 복지사 대시보드 (React + Vite + TypeScript)
├── mobile/           ← 모바일 앱 (Expo React Native)
├── docker-compose.yml
└── .env.example
```

---

## 파이프라인 목록

| # | 파이프라인 | 상태 | 문서 |
|---|-----------|------|------|
| A | 공공데이터 수집 · 주제 선정 | 계획 | [plan_A_public-data.md](../../../plan/reference/pipeline-A/plan_A_public-data.md) |
| A' | 복지사 중심 주제 선정 | 계획 | [plan_A-prime_welfare-topic.md](../../../plan/reference/pipeline-A/plan_A-prime_welfare-topic.md) |
| A'' | 설문지 통합 관리 | 계획 | [plan_A-dblprime_survey-integration.md](../../../plan/reference/pipeline-A/plan_A-dblprime_survey-integration.md) |
| B | 사용자 대화 (STT→AI→TTS) | 계획 | [plan_B_user-chat.md](../../../plan/reference/pipeline-B/plan_B_user-chat.md) |
| C | 감정 분석 · 심리 지표 | 계획 | [plan_C_emotion-analysis.md](../../../plan/reference/pipeline-C/plan_C_emotion-analysis.md) |
| D | 수필 생성 · 배포 | 계획 | [plan_D_essay-generation.md](../../../plan/reference/pipeline-D/plan_D_essay-generation.md) |
| E | 안전 감지 · 긴급 대응 | 계획 | [plan_E_safety-detection.md](../../../plan/reference/pipeline-E/plan_E_safety-detection.md) |
| F | 복지사 알림 · 대시보드 | 계획 | [plan_F_welfare-worker.md](../../../plan/reference/pipeline-F/plan_F_welfare-worker.md) |
| G | 데이터 보안 (횡단) | 계획 | [plan_G_security.md](../../../plan/reference/pipeline-G/plan_G_security.md) |

---

## 작업 유형별 문서

| 작업 유형 | 참조 문서 |
|-----------|----------|
| 전체 통합 구현 | [plan/이음_통합구현계획_20260604.md](../../plan/이음_통합구현계획_20260604.md) |
| 시나리오 테스트 | [plan/reference/이음_시나리오테스트.md](../../plan/reference/이음_시나리오테스트.md) |
| 재검증 보고서 | [plan/reference/이음_재검증보고서_전체.md](../../plan/reference/이음_재검증보고서_전체.md) |
| 빠른 시작 | [ium/README.md](../../ium/README.md) |
| 공통 개발 표준 | [.clinerules/docs/development/](.clinerules/docs/development/) |

---

## ⚙️ 수정 가이드

- 이 문서는 프로젝트의 **나침반** 역할만 함
- 새로운 파이프라인이 추가되면 이 문서에 행 추가
- 파이프라인 상세는 각 `plan/reference/pipeline-X/plan_X_*.md` 파일 참조
- 80줄 초과 시 하위 문서로 분리 후 경로만 남길 것