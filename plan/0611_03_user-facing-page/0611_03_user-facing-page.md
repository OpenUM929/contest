> 상태: EXE | 작성일: 2026-06-11 | 최종 업데이트: 2026-06-18

# 사용자(노인/청년) 화면 구현 계획

---

## 1. 개요

**목표**: 사용자(노인/청년) 전용 화면 구현. 복지사 대시보드와 분리된 별도 페이지.

**핵심 원칙**:
- 관리자가 아닌 사용자가 접속하면 **관리자 대시보드가 아닌 자신의 설문/통계/콘텐츠 화면**이 보여야 함
- **설문과 통계가 연결**: 자신이 응답한 설문에 대해서만 통계 제공
- **심리지수는 관리자 전용**: 사용자 화면에서 노출하지 않음

---

## 2. 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| — | — | 초안 작성 |
| 2026-06-18 | §3, §4, §5, §6, §9 | 설문 답변 제출/수정 기능 추가, 통계 정보 카드 표시, API 추가 |
| 2026-06-18 | §3-5, §5-2, §6-2, §9 | STT(음성→텍스트) 버튼 추가, 접근성 개선 |
| 2026-06-18 | §10 | 대시보드 404 이슈 수정 (라우트 등록 순서 문제 해결) |

---

## 3. 요구사항

### 3-1. 설문 + 통계 (연결된 구조)
- **설문 목록**: 모든 설문(응답/미응답 포함)을 카드로 표시
  - 응답 완료: ✅ 태그 + 간단 통계(참여자 수, 응답률)
  - 미응답: 📝 태그 + "설문 참여하기" 버튼
- **미응답 설문 클릭 → 설문 답변 폼**:
  - 설문지의 모든 질문(선택형/서술형)을 폼으로 표시
  - 선택형: 라디오 버튼으로 옵션 선택
  - 서술형: 텍스트 영역에 자유 입력
  - 제출 → `POST /api/chat/surveys/{topic_id}/respond` 호출
- **응답 완료 설문 클릭 → 내 응답 + 통계 + 수정**:
  - 내 응답 내용 확인 (해당 질문별로 표시)
  - **해당 설문의 통계** 함께 표시 (전체 % + 내 응답 위치)
  - 수정 버튼 → 같은 폼에 기존 응답이 채워진 상태로 편집
- **선택형**: 옵션별 바 차트 + 내 선택 강조
- **서술형**: 내 응답 전문 + 다른 사람 응답 샘플(익명)

### 3-2. UX: 편하게 (노인/청년 모두)
- **큰 글씨**: 폰트 16px 기준, 제목 24px
- **대화면**: 카드형 레이아웃, 터치/클릭 영역 넉넉히
- **간단한 탭**: 3개 탭만 (설문/콘텐츠/내정보)
- **색상 대비**: 배경 #FFFDF7, 강조 #E8572A, 텍스트 #4A3728
- **모바일 대응**: 반응형 (모바일에서도 사용 가능)

### 3-3. 콘텐츠 (모듈형, 확장 준비)
- **지금**: 수필(에세이) 목록 + 읽기
- **향후**: 문학집, 사진전, 활동 보고 등 모듈 추가 가능
- **구조**: 모듈 정의 JSON + 렌더러 함수로 분리

### 3-4. 내 정보 (간단하게)
- 닉네임, 유형(노인/청년), 가입일
- **심리지수**: ❌ 노출하지 않음 (관리자 전용)
- **안전 상태**: 최근 알림 유무 (간단히)
- **마지막 접속**: 날짜 표시

### 3-5. 접근성: STT (음성 → 텍스트)
- **목적**: 노인 사용자가 글쓰기에 어려움을 느끼는 경우 음성으로 답변 입력
- **적용 대상**: 설문 서술형(narrative) 질문의 textarea
- **동작**:
  - textarea 아래 `[🎤 음성으로 말하기]` 버튼
  - 클릭 → 브라우저 `MediaRecorder` API로 녹음 시작
  - 최대 **30초** 녹음, 타이머 표시
  - 녹음 완료 → `POST /api/chat/voice/stt`로 음성 전송
  - 변환된 텍스트를 textarea에 자동 삽입 (기존 텍스트 뒤에 추가)
  - 제출은 수동 (자동 제출 안 함)
- **녹음 상태**: 버튼 색상/텍스트 변경, 초 단위 타이머

---

## 4. API 설계

### 4-1. 기존 API (그대로 사용)

| Endpoint | 용도 | 기존 |
|----------|------|------|
| `GET /api/chat/users/{user_id}/my-surveys` | 설문 이력 | ✅ 이미 존재 |
| `GET /api/essay/` | 에세이 목록 | ✅ 이미 존재 |
| `GET /api/essay/{essay_id}` | 에세이 상세 | ✅ 이미 존재 |
| `GET /api/safety/check/{user_id}` | 안전 상태 | ✅ 이미 존재 |

### 4-2. 추가 API (신규)

| Endpoint | 용도 | 설명 |
|----------|------|------|
| `GET /api/chat/users/{user_id}/profile` | 사용자 프로필 | 닉네임, 유형, 가입일, 마지막 접속 |
| `GET /api/chat/surveys/{topic_id}/my-analytics?user_id={user_id}` | **내 통계** | 해당 설문 전체 통계 + 내 응답 포함 |
| `GET /api/chat/content` | 콘텐츠 라이브러리 | 에세이 + 모듈별 콘텐츠 목록 |
| `POST /api/chat/surveys/{topic_id}/respond` | 설문 답변 제출 | AI 대화 없이 순수 응답 저장 |
| `PUT /api/chat/surveys/{topic_id}/respond` | 설문 답변 수정 | 기존 응답 덮어쓰기 (이력 미보존) |

### 4-4. `POST/PUT /api/chat/surveys/{topic_id}/respond` 세부 설계

```
POST /api/chat/surveys/{topic_id}/respond
Body:
{
  "user_id": "...",
  "responses": [
    {
      "question_id": "q1",
      "question_type": "choice",
      "selected_option_id": "opt_1",
      "selected_option_label": "예"
    },
    {
      "question_id": "q2",
      "question_type": "narrative",
      "narrative_text": "자유롭게 쓴 내용..."
    }
  ]
}

Response:
{
  "status": "ok",
  "topic_id": "...",
  "response_count": 2
}
```

> PUT은 POST와 동일한 Body 형식. 기존 해당 사용자의 SurveyResponse를 모두 삭제 후 새로 저장 (덮어쓰기).

### 4-3. `my-analytics` 세부 설계

```
GET /api/chat/surveys/{topic_id}/my-analytics?user_id={user_id}

Response:
{
  "topic_id": "...",
  "topic_title": "...",
  "total_respondents": 42,
  "my_participated": true,
  "my_responses": [
    {
      "question_id": "q1",
      "question_text": "시장에서 가장 기억에 남는 것은?",
      "question_type": "choice",
      "my_answer": "채소·생선 좌판",
      "statistics": [
        {"label": "채소·생선 좌판", "count": 15, "percent": 35.7},
        {"label": "옷감·천 가게", "count": 12, "percent": 28.6},
        {"label": "떡집·분식", "count": 8, "percent": 19.0},
        {"label": "기타", "count": 7, "percent": 16.7},
      ]
    }
  ]
}
```

> 기존 `/api/welfare/surveys/{topic_id}/analytics` 로직을 재사용하되:
> 1. `user_id`로 해당 사용자의 응답 포함
> 2. 사용자가 응답하지 않은 설문은 403 반환

---

## 5. UI 화면 구성

### 5-1. 전체 레이아웃 (3탭)

```
┌─────────────────────────────────────────────┐
│  👤 {닉네임} (노인/청년)     🔄 계정 전환    │
├─────────────────────────────────────────────┤
│                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │  📋 설문  │  │  📚 콘텐츠 │  │  👤 내 정보 │  │
│   └──────────┘  └──────────┘  └──────────┘  │
│                                             │
│   [탭 콘텐츠]                                │
│                                             │
└─────────────────────────────────────────────┘
```

### 5-2. 📋 설문 탭 (Survey + Stats + Answer)

**목록 화면**:
- 모든 설문 카드 표시 (응답/미응답 구분)
- 각 카드: 이미지(또는 대체 아이콘), 제목, 주차, 응답 상태(✅응답완료/📝미응답)
- 응답 완료 카드: 추가로 참여자 수 표시 ("15/42명 응답")
- 미응답 카드: "설문 참여하기" 배지

**설문 답변 폼 (미응답 클릭 시 모달)**:
- 설문지 제목 + 설명 표시
- 질문 목록 (선택형: 라디오 버튼 / 서술형: 텍스트 영역)
- 서술형 질문: textarea 아래 `[🎤 음성으로 말하기]` 버튼 (STT)
  - 녹음 시 빨간 점 애니메이션 + 타이머
  - 30초 초과 시 자동 종료
  - 변환 완료 시 textarea에 텍스트 자동 입력
- 각 질문에 답변 입력
- "제출하기" 버튼 → 제출 후 통계 화면으로 전환

**응답 + 통계 상세 화면 (응답 완료 클릭 시 모달)**:
- 상단: 주제 이미지(optional) + 제목 + 주차 + 총 응답 개수
- 중간: 질문별 내 응답 + 통계 (바 차트)
  - 내 응답 강조 표시 (노랑)
  - 전체 통계와 비교
- 하단: 다른 사람 서술형 응답 샘플 (익명)
- **"수정하기" 버튼** → 답변 폼 모달로 전환 (기존 응답 채워짐)

### 5-3. 📚 콘텐츠 탭 (Content)

**수필/에세이 목록**:
- 카드: 주제, 날짜, 기여자 수
- 클릭 → 모달로 전문 읽기

**확장 모듈 (미래)**:
```javascript
const modules = {
  essay: { title: "수필", icon: "📖", endpoint: "/api/essay/" },
  anthology: { title: "문학집", icon: "📚", endpoint: "/api/anthology/" },
  // 추후 추가
};
```

### 5-4. 👤 내 정보 탭 (My Info)

- 닉네임, 유형, 가입일, 마지막 접속
- 안전 상태: 🟢 정상

---

## 6. 구현 파일

### 6-1. Backend

| 파일 | 작업 | 설명 |
|------|------|------|
| `backend/app/routers/chat.py` | 수정 | `GET /users/{user_id}/profile` 추가 |
| `backend/app/routers/chat.py` | 수정 | `GET /surveys/{topic_id}/my-analytics` 추가 |
| `backend/app/routers/chat.py` | 수정 | `GET /content` 추가 (콘텐츠 라이브러리) |
| `backend/app/routers/chat.py` | 수정 | `POST /surveys/{topic_id}/respond` 추가 (설문 제출) |
| `backend/app/routers/chat.py` | 수정 | `PUT /surveys/{topic_id}/respond` 추가 (설문 수정) |

### 6-2. Frontend

| 파일 | 작업 | 설명 |
|------|------|------|
| `backend/app/static/user.html` | 수정 | STT 버튼 + 녹음 로직 + STT API 호출 추가 (서술형 질문)

---

## 7. 로그인 흐름

```
1. /login.html 접속
2. 계정 선택 (노인/청년/관리자)
3. 로그인 API 호출
4. localStorage 저장: user_id, user_type, nickname
5. user_type === "admin" ? redirect("/") : redirect("/user.html")
```

---

## 8. UX 상세

### 8-1. 폰트/크기
- 기본: 16px (모바일), 18px (데스크탑)
- 제목: 24px
- 작은 텍스트: 14px
- 카드 패딩: 20px
- 버튼: 최소 48px 높이

### 8-2. 색상
- 배경: `#FFFDF7` (크림)
- 카드: `#FFFFFF`
- 텍스트: `#4A3728` (갈색)
- 강조: `#E8572A` (주황)
- 보조: `#FFB800` (노랑)
- 안전: `#22C55E` (초록)
- 경고: `#EF4444` (빨강)

### 8-3. 인터랙션
- 카드 hover: 그림자 증가 + 약간 위로 이동
- 클릭: 상세 화면 슬라이드/페이드
- 뒤로가기: 상단 고정
- 로딩: 스피너 (중앙)

---

## 9. 구현 순서

1. **Backend API**: `profile`, `my-analytics`, `content` 추가 (완료 ✅)
2. **Backend API**: `POST /surveys/{topic_id}/respond`, `PUT /surveys/{topic_id}/respond` 추가
3. **login.html**: 리다이렉트 분기 (admin → /dashboard, user → /user)
4. **main.py**: `/dashboard` 라우트 추가, StaticFiles html=True 제거
5. **user.html**:
   - HTML/CSS 프레임 (3탭)
   - 설문 목록 (응답/미응답 구분, 통계 정보 포함)
   - 설문 답변 폼 (선택형/서술형 질문)
   - 설문 응답 + 통계 상세 (내 답변 + 통계 바 차트)
   - 응답 수정 기능 (기존 응답 채워진 폼)
   - 콘텐츠 탭 (수필)
   - 내 정보 탭
6. **테스트**:
   - 로그인 → user.html 이동
   - 미응답 설문 → 답변 제출 → 통계 확인
   - 응답 완료 설문 → 통계 확인 → 수정
   - 콘텐츠 → 수필 읽기
   - 내 정보 확인

---

## 10. 트러블슈팅: 대시보드 404 이슈

> **증상**: `GET /dashboard HTTP/1.1` → 404 Not Found

**원인**: `main.py`에서 라우트 등록 순서 문제.

```python
# ① 먼저 등록됨 — 모든 경로를 가로챔 (catch-all)
app.mount("/", StaticFiles(directory=_dash_dir), name="dashboard")

# ② 나중에 등록됨 — ①이 먼저 매칭되므로 절대 호출되지 않음
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    ...
```

FastAPI/Starlette는 라우트를 **등록 순서대로** 매칭한다.  
`app.mount("/", ...)`는 `/` 아래 모든 경로와 매칭되므로, `/dashboard` 요청도 이 mount가 먼저 가로챈다.  
Mount는 `_dash_dir`에서 `dashboard`라는 이름의 파일/디렉토리를 찾고, 없으면 404를 반환한다.

**해결**: 두 선언의 순서를 변경한다.

```python
if _dash_exists:
    # ① 먼저: 명시적 라우트 (mount가 가로채기 전에 매칭)
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_page():
        ...
    # ② 나중: 정적 파일 마운트
    app.mount("/", StaticFiles(directory=_dash_dir), name="dashboard")
```

**왜 `app.mount("/dashboard", ...)`를 안 쓰는가?**  
대시보드의 `index.html`이 `/assets/...` (절대경로)로 에셋을 참조하기 때문.  
루트 마운트(`/`)여야 `/assets/...`가 정상 서빙된다.

---

**계획 승인 시 "수행"이라고 말해 주세요. 그때까지 실행하지 않습니다.**

---

## 참조

- `plan/0611_02_temp-login-hardcoded/0611_02_temp-login-hardcoded.md` — 임시 로그인 구현 (관련)
- `backend/app/routers/chat.py` — 기존 사용자 API
- `backend/app/routers/welfare.py` — 기존 통계/설문 API
- `backend/app/routers/essay.py` — 기존 수필 API