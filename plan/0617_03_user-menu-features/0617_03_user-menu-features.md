> 상태: PND | 작성일: 2026-06-17

# 노인/청년 사용자 메뉴 개편: 설문지 관리 · 통계 · 결과물 전달

---

## 1. 개요

**목표**: 모바일 앱(ElderlyMain/YouthMain)의 하단 메뉴를 기존 3개(`지난 이야기 듣기`/`내가 나눈 이야기`/`다른 이들의 생각`)에서 **설문지 관리** · **통계** · **결과물 전달** 3개로 전면 교체한다.

**배경**: 노인/청년 사용자가 접속했을 때 복지사가 제공한 설문에 참여하고, 그룹 통계를 확인하며, 복지사가 생성한 결과물(수필/시/소설)을 받을 수 있어야 함.

---

## 2. 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| — | — | 초안 작성 |

---

## 3. 요구사항

### 3-1. 설문지 관리
- 복지사가 제공한 설문지(**WeeklyTopic**)를 모두 카드로 표시
- 기존/신규 구분: 내가 답변한 적이 있으면 `작성완료`, 없으면 `신규` 배지
- 카드 터치 시 설문으로 진입하여 답변/수정 가능
- 이미 답변한 설문도 재진입하여 추가 답변 가능
- AI 대화(챗봇)와 연결된 설문 UX 유지

### 3-2. 통계 (내 그룹 통계)
- 내가 참여한 설문에 대해, **해당 설문의 전체 참여자**들의 응답 통계 제공
- **선택형**: 각 선택지별 선택 수 + 백분율
- **서술형**: 익명 샘플 답변 목록 (최신순 3~10개)
- **내 답변**: 나의 선택/내가 쓴 답변 강조 표시
- 이미 구현된 `GET /chat/surveys/{topic_id}/my-analytics` API 활용

### 3-3. 결과물 전달
- 복지사가 생성한 결과물 목록 (수필 외 시/소설 등)
- `content_type`으로 유형 구분 (essay / poem / novel)
- 각 카드: 제목, 유형, 참여자 수, 발행일
- 상세: 전문 읽기 + Elderly용 TTS 읽어듣기

---

## 4. 백엔드 설계

### 4-1. 데이터 모델 변경

**`Essay` 테이블에 `content_type` 컬럼 추가**

| 컬럼 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `content_type` | String(20) | `"essay"` | 결과물 유형: essay, poem, novel |

### 4-2. 신규 API

| Method | Endpoint | 용도 |
|--------|----------|------|
| `GET` | `/api/chat/users/{user_id}/available-surveys` | 사용자에게 배포된 모든 WeeklyTopic 목록 + 답변 여부 |
| `GET` | `/api/chat/topics/{topic_id}` | 특정 주제 상세 조회 (과거 주제 로드용) |

### 4-3. 수정 API

| Method | Endpoint | 변경 내용 |
|--------|----------|-----------|
| `POST` | `/api/chat/message` | body에 `topic_id` 필드 추가 (선택). 과거 주제에도 답변 저장 가능 |
| `GET` | `/api/chat/users/{user_id}/my-surveys` | `has_responded` 필드 추가 (선택 사항) |
| `GET` | `/api/essay/archive` | `content_type` 응답에 포함. 쿼리 파라미터 `type`으로 필터링 지원 |

### 4-4. `available-surveys` 응답 예시

```json
{
  "user_id": "uuid",
  "surveys": [
    {
      "topic_id": "uuid",
      "title": "옛날 시장 풍경",
      "active_week": "2026-06-15",
      "question_type": "mixed",
      "media_url": "https://...",
      "has_responded": true,
      "responded_at": "2026-06-16T10:00:00"
    },
    {
      "topic_id": "uuid",
      "title": "우리 동네 봄 축제",
      "active_week": "2026-06-22",
      "question_type": "choice",
      "media_url": null,
      "has_responded": false,
      "responded_at": null
    }
  ]
}
```

### 4-5. 메시지 저장 수정 (`POST /chat/message`)

```python
class ChatRequest(BaseModel):
    user_id: str
    message: str
    topic_id: str | None = None  # NEW: 특정 주제 ID (과거 주제 재참여)
    question_id: str | None = None
    selected_option_id: str | None = None
    selected_option_label: str | None = None
```

- `topic_id`가 없으면 현재 활성 주제 사용 (기존 동작)
- `topic_id`가 있으면 해당 주제에 답변 저장
- AI 응답 컨텍스트는 기존과 동일한 대화 이력 사용

---

## 5. 모바일 API 클라이언트 (`mobile/api/survey.ts`)

| 함수 | 설명 |
|------|------|
| `fetchAvailableSurveys(userId)` | `/chat/users/{userId}/available-surveys` 호출 |
| `fetchTopicById(topicId)` | `/chat/topics/{topicId}` 호출 |
| `fetchTopicStatistics(topicId, userId)` | `/chat/surveys/{topicId}/my-analytics?user_id={userId}` 호출 |
| `fetchDeliverablesArchive(type?)` | `/essay/archive?type={type}` 호출 (content_type 필터) |
| `submitChatWithTopic(payload)` | 기존 `submitChat`에 `topic_id` 포함 확장 |

---

## 6. 모바일 UI 화면 구성

### 6-1. 공통 구조 (ElderlyMain / YouthMain)

```
┌─────────────────────────────────────┐
│  [헤더 + 이번 주 주제 + 설문 영역]    │  ← 기존 유지
├─────────────────────────────────────┤
│                                     │
│  [하단 메뉴: 3개 버튼]              │
│  ┌─────────┐ ┌────────┐ ┌────────┐  │
│  │ 설문지   │ │ 통계   │ │ 결과물  │  │
│  │ 관리     │ │ 보기   │ │ 전달   │  │
│  └─────────┘ └────────┘ └────────┘  │
│                                     │
│  [계정 전환 / 글자 크기]             │
└─────────────────────────────────────┘
```

### 6-2. 설문지 관리 모달

```
┌─ ← 닫기   설문지 관리 ──────────────┐
│                                      │
│  ┌────────────────────────────────┐  │
│  │ [작성완료] 옛날 시장 풍경      │  │
│  │ 📅 6월 3주차                   │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ [신규]    우리 동네 봄 축제    │  │
│  │ 📅 6월 4주차                   │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ [작성완료] 옛날 시장 풍경      │  │
│  │ 📅 6월 2주차                   │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### 6-3. 통계 모달

```
┌─ ← 닫기   통계 보기 ────────────────┐
│                                      │
│  [내가 참여한 설문 중 선택]           │
│  ┌────────────────────────────────┐  │
│  │ 옛날 시장 풍경 — 15명 참여     │  │
│  └────────────────────────────────┘  │
│                                      │
│  ── 질문 1: 가장 기억에 남는 것은? ── │
│  나의 선택: 채소·생선 좌판 ✓         │
│                                      │
│  ████████████ 채소·생선 좌판 35.7%  │
│  ██████████  옷감·천 가게   28.6%  │
│  ██████      떡집·분식     19.0%  │
│  ██████      기타          16.7%  │
│                                      │
│  ── 질문 2: 자유로운 이야기 ───────── │
│  총 12명이 답변했어요                │
│                                      │
│  📝 "어릴 적 엄마 따라..."           │
│  📝 "시장 아주머니가..."             │
│  📝 "김밥 한 줄이..."                │
└──────────────────────────────────────┘
```

### 6-4. 결과물 전달 모달

```
┌─ ← 닫기   결과물 전달 ──────────────┐
│                                      │
│  ┌────────────────────────────────┐  │
│  │ 📖 수필 「옛날 시장의 추억」   │  │
│  │ 👥 15명의 이야기 · 6월 3주차  │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ 📝 시   「봄날의 시장 노래」   │  │
│  │ 👥 12명의 이야기 · 6월 2주차  │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ 📖 소설 「시장, 그곳에 사람」  │  │
│  │ 👥 20명의 이야기 · 6월 1주차  │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### 6-5. 설문 재참여 플로우

```
설문지 관리 → 카드 선택
  │
  ├─ has_responded == false → 신규 설문
  │     └─ ElderlySurvey / YouthSurvey 표시 (topic_id 주입)
  │           └─ 답변 → chat/message (topic_id 포함)
  │
  └─ has_responded == true → 기존 설문 재참여
        └─ Alert: "이전에 작성한 답변 위에 새로운 답변을 추가합니다"
              └─ ElderlySurvey / YouthSurvey 표시
                    └─ 추가 답변 → chat/message (topic_id 포함)
```

---

## 7. 구현 파일 및 작업

### 7-1. Backend

| 파일 | 작업 | 설명 |
|------|------|------|
| `backend/app/models/models.py` | 수정 | `Essay.content_type` 컬럼 추가 |
| `backend/app/routers/chat.py` | 수정 | `GET /users/{user_id}/available-surveys` 신규 |
| `backend/app/routers/chat.py` | 수정 | `GET /topics/{topic_id}` 신규 |
| `backend/app/routers/chat.py` | 수정 | `POST /message`에 `topic_id` 필드 추가 |
| `backend/app/routers/essay.py` | 수정 | `GET /archive`에 `content_type` 포함 및 필터 |
| — | Alembic 마이그레이션 | `essay.content_type` 컬럼 추가 |

### 7-2. Mobile

| 파일 | 작업 | 설명 |
|------|------|------|
| `mobile/api/survey.ts` | 수정 | API 함수 4개 추가 + `topic_id` 파라미터 확장 |
| `mobile/screens/ElderlyMain.tsx` | 수정 | 메뉴 교체, 모달 3종, 설문 재참여 로직 |
| `mobile/screens/YouthMain.tsx` | 수정 | ElderlyMain과 동일 패턴 (청년 스타일 적용) |

### 7-3. None (신규 파일 없음)

---

## 8. 구현 순서

```
Phase 1: Backend 모델 + API
  ├─ Essay.content_type 추가 (모델 + 마이그레이션)
  ├─ available-surveys API 신규
  ├─ topics/{topic_id} API 신규
  ├─ chat/message topic_id 확장
  └─ essay/archive content_type 반영

Phase 2: Mobile API 클라이언트
  ├─ survey.ts에 함수 추가
  └─ submitChat 확장

Phase 3: ElderlyMain UI
  ├─ 하단 메뉴 교체 (3개)
  ├─ 설문지 관리 모달
  ├─ 통계 모달
  ├─ 결과물 전달 모달
  └─ 설문 재참여 플로우 연결

Phase 4: YouthMain UI
  └─ ElderlyMain과 동일 패턴 (Youth 스타일)

Phase 5: 통합 테스트
  └─ 전체 플로우 E2E 검증
```

---

## 9. 참고 사항

### 9-1. 이미 구현된 사항
- `GET /chat/surveys/{topic_id}/my-analytics` (사용자용 통계) → `chat.py:311` **이미 구현 완료**
- `GET /welfare/surveys/{topic_id}/analytics` (복지사용 통계) → `welfare.py:1015`
- `GET /chat/users/{user_id}/my-surveys` (내 설문 목록) → `chat.py:246`
- `GET /essay/archive` (수필 아카이브) → `essay.py:107`

### 9-2. Essay 모델 확장 설계
```python
class Essay(Base):
    __tablename__ = "essays"
    # 기존 컬럼 유지
    content_type: Mapped[str] = mapped_column(String(20), default="essay")
    # essay, poem, novel, report 등
```

### 9-3. 고려사항
- 과거 주제 답변 시 `POST /chat/message`의 AI 응답은 현재 주제 기반 컨텍스트를 사용하되, `topic_id` 정보를 프롬프트에 포함시켜 일관성 유지
- 통계의 타인 답변 `user_id != current_user_id`로 필터링되어 익명 보장
- 설문 재참여 시 **추가 답변(append)** 방식 (기존 답변 유지 + 새로운 답변 추가)

---

## 10. 참조

- `plan/0611_03_user-facing-page/0611_03_user-facing-page.md` — 사용자 화면 구현 기획 (관련)
- `backend/app/routers/chat.py` — 사용자 API 라우터
- `backend/app/routers/welfare.py` — 복지사 API (통계 참조)
- `backend/app/routers/essay.py` — 수필 API
- `backend/app/models/models.py` — 데이터 모델
- `mobile/screens/ElderlyMain.tsx` — 노인 메인 화면
- `mobile/screens/YouthMain.tsx` — 청년 메인 화면
- `mobile/api/survey.ts` — 모바일 API 클라이언트
- `mobile/types/survey.ts` — 모바일 타입 정의
