# 계정·로그인 일관성 개선 및 복지사-사용자 할당 체계 구축

> 상태: PND | 작성일: 2026-06-18 | 작업 유형: DB 기반 계정 전환 + 할당 체계 정립

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|----------|
| 2026-06-18 | 전체 초안 | 최초 작성 |

---

## 1. 현재 문제 분석

### 1-1. 하드코딩된 TEMP_ACCOUNTS

**현재:** `TEMP_ACCOUNTS` 딕셔너리가 백엔드/프론트엔드 3곳에 중복 하드코딩

| 파일 | 내용 | 문제 |
|------|------|------|
| `backend/app/routers/auth.py:13-22` | `TEMP_ACCOUNTS` 정의 | DB 무시, 코드에 의존 |
| `mobile/screens/LoginScreen.tsx:10-17` | 동일 계정 목록 드롭다운 | 백엔드와 별도 관리, 동기화 누락 |
| `backend/app/static/login.html:97-115` | 동일 계정 목록 `<select>` | 동일 문제 |

**결과:** 계정 수정 시 3곳을 동시에 바꿔야 함. 실제 DB 데이터와 무관한 허상 구조.

### 1-2. 가짜 DB 조회 로직

`auth.py:temp_login()`:
1. `temp_id`로 `TEMP_ACCOUNTS` 조회 (코드)
2. `user_type`이 `worker` → `name`으로 `WelfareWorker` SELECT → 없으면 **자동 생성**
3. `user_type`이 `elder/youth` → `nickname`으로 `User` SELECT → 없으면 **자동 생성**
4. 복지사 없으면 `SELECT WelfareWorker LIMIT 1`로 **임의 연결**

### 1-3. 복지사-사용자 할당 부재 (핵심 문제)

```
                 ┌─→ ???(무작위 복지사 연결)
  사용자 로그인 ──┤
                 └─→ ???(다른 복지사 영역의 데이터 노출)
```

**영향:**
- 복지사 A의 담당 사용자가 복지사 B에게 할당될 수 있음
- 복지사 대시보드에 엉뚱한 사용자가 표시됨
- 주제 배포 시 `welfare_id` 기준 격리가 깨짐
- 통계 집계 시 권한 밖의 데이터가 포함됨

### 1-4. Admin 계정 부재

`admin.py:22`:
```python
ADMIN_ID = "admin"  # 하드코딩
```

DB에 관리자 레코드가 없어 `admin_logs`의 추적이 무의미.

### 1-5. 인증 부재

JWT/세션 없음. `localStorage`에 `temp_user_id`만 저장.  
API 호출 시 아무 `user_id`나 사용 가능.

---

## 2. 목표 아키텍처

```
┌────────────────────┐         ┌──────────────────────────────┐
│    Mobile App      │         │       Backend (FastAPI)      │
│  (React Native)    │────POST─→  POST /api/auth/login       │
│                    │  /login  │      ↓                      │
│   ID/PW 입력       │         │   SQLite DB 조회             │
│                    │←──JWT── │   (users / welfare_workers)  │
└────────────────────┘         │      ↓                      │
                               │   응답: user_id, user_type,  │
┌────────────────────┐         │   nickname, welfare_id, etc  │
│   Dashboard (Web)  │───────→│                              │
│  (React + Vite)    │  API    │   이후 모든 API는             │
│                    │  호출    │   user_id + welfare_id 기반  │
└────────────────────┘         └──────────────────────────────┘
                                        ↑
                               ┌────────┴────────┐
                               │    SQLite DB      │
                               │  local_ium.db     │
                               │                   │
                               │  welfare_workers  │
                               │  users            │
                               │  (미리 시드)       │
                               └──────────────────┘
```

### 2-1. 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **DB가 유일한 Source of Truth** | 모든 계정 정보는 SQLite에만 존재. 코드 하드코딩 제로 |
| **명시적 할당** | 복지사-사용자 연결은 Admin/복지사가 API로 직접 수행 |
| **welfare_id 격리** | 모든 데이터 조회 시 `welfare_id` 기준 필터링 |
| **로그인 = DB 조회** | 자동 생성 금지, 미리 시드된 계정만 허용 |

---

## 3. 계정 정보 구성 (SQLite 시드)

### 3-1. welfare_workers 테이블 시드

```sql
-- 관리자 (admin)
INSERT INTO welfare_workers (id, name, email, phone, password_hash, role, region, status)
VALUES 
  ('a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d', '관리자', 'admin@ium.kr', '010-0000-0000', 'admin1234', 'admin', '서울특별시', 'active');

-- 복지사 (worker)
INSERT INTO welfare_workers (id, name, email, phone, password_hash, role, region, status)
VALUES 
  ('b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e', '김복지', 'kim@welfare.kr',  '010-1000-0001', 'demo1234', 'worker', '서울 종로구', 'active'),
  ('c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f', '이복지', 'lee@welfare.kr',  '010-1000-0002', 'demo1234', 'worker', '경기 수원시', 'active');
```

### 3-2. users 테이블 시드

```sql
-- 김복지(b1c2...) 담당 사용자
INSERT INTO users (id, user_type, name, nickname, email, phone, password_hash, welfare_id, status, is_anonymous)
VALUES 
  ('u1000000-0000-4000-a000-000000000001', 'elder', '김길동',  '김어르신', 'elder1@test.kr', '010-1111-0001', 'demo1234', 'b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e', 'active', false),
  ('u1000000-0000-4000-a000-000000000002', 'elder', '박말순',  '박어르신', 'elder2@test.kr', '010-1111-0002', 'demo1234', 'b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e', 'active', false),
  ('u1000000-0000-4000-a000-000000000003', 'youth', '최민수',  '김청년',   'youth1@test.kr', '010-2222-0001', 'demo1234', 'b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e', 'active', true),
  ('u1000000-0000-4000-a000-000000000004', 'youth', '이영희',  '이청년',   'youth2@test.kr', '010-2222-0002', 'demo1234', 'b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e', 'active', true),
  ('u1000000-0000-4000-a000-000000000005', 'youth', '박지수',  '박청년',   'youth3@test.kr', '010-2222-0003', 'demo1234', 'b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e', 'active', true);

-- 이복지(c1d2...) 담당 사용자
INSERT INTO users (id, user_type, name, nickname, email, phone, password_hash, welfare_id, status, is_anonymous)
VALUES 
  ('u2000000-0000-4000-a000-000000000001', 'elder', '최옥순',  '최어르신', 'elder3@test.kr', '010-1111-0003', 'demo1234', 'c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f', 'active', false);
```

### 3-3. 시드 데이터 관계도

```
관리자(admin) ─── 시스템 전반 관리, 복지사/사용자 CRUD
      │
      ├─── 김복지(worker, 서울 종로구)
      │       ├─── 김어르신(elder)
      │       ├─── 박어르신(elder)
      │       ├─── 김청년(youth)
      │       ├─── 이청년(youth)
      │       └─── 박청년(youth)
      │
      └─── 이복지(worker, 경기 수원시)
              └─── 최어르신(elder)
```

> **각 사용자는 로그인 시 무조건 자신의 `welfare_id`에 할당된 복지사만 조회 가능.**

---

## 4. 복지사-사용자 할당 체계 (이 부분이 누락되어 있었음)

### 4-1. 할당 흐름도

```
[관리자 웹] 사용자 등록                        [관리자 웹] 복지사 등록
  POST /api/admin/users                         POST /api/admin/workers
  └─→ welfare_id 선택 가능                       └─→ role: admin | worker
      (드롭다운에서 복지사 선택)
         ↓
[관리자 웹] 사용자 목록 → 배정/재배정
  POST /api/admin/users/{user_id}/assign        ← 개별 배정
  POST /api/admin/workers/{welfare_id}/assign   ← 복지사 기준 일괄 배정
         ↓
[DB] users.welfare_id 갱신
         ↓
[사용자 로그인] → GET /api/chat/users/{id}/available-surveys
         ↓
  자신의 welfare_id 기준으로 weekly_topics 필터링
  → 담당 복지사가 발행한 주제만 표시
```

### 4-2. 할당 API 정리 (이미 존재)

| API | Method | 설명 | 위치 |
|-----|--------|------|------|
| `/api/admin/users/{user_id}/assign` | POST | 개별 사용자의 복지사 배정/재배정 | `admin.py:318` |
| `/api/admin/workers/{welfare_id}/assign` | POST | 복지사에 회원 일괄 배정 | `admin.py:378` |
| `/api/admin/workers/{welfare_id}/unassign` | POST | 복지사에서 회원 일괄 해제 | `admin.py:408` |
| `/api/admin/workers/{welfare_id}/users` | GET | 복지사 배정 회원 목록 | `admin.py:351` |
| `/api/admin/users` | POST | 사용자 등록 시 welfare_id 직접 지정 | `admin.py:171` |

**⚠️ 이 API들은 이미 코드에 존재하지만, 현재 더미 로그인 구조와 연결되지 않아 실효성이 없음.**
Phase 1 수정 후 이 API들이 실제로 의미 있게 동작하게 됨.

### 4-3. Dashboard UI 요구사항 (Admin 페이지)

현재 Dashboard에 Admin 페이지가 있지만, 복지사 할당 UI가 프론트엔드에 구현되어 있지 않을 가능성이 높음.  
아래 UI 컴포넌트가 필요:

| 화면 | 필요 기능 | 대상 파일 (추정) |
|------|----------|-----------------|
| 사용자 상세/수정 | `welfare_id` 드롭다운 선택 | `dashboard/src/pages/admin/` |
| 사용자 목록 | 복지사 필터 + 할당 버튼 | `dashboard/src/pages/admin/` |
| 복지사 상세 | 담당 사용자 목록 + 일괄 배정 | `dashboard/src/pages/admin/` |
| 일괄 작업 | 여러 사용자 선택 → 복지사 지정 | `dashboard/src/pages/admin/` |

---

## 5. 설문지(주제) 배포 및 통계 플로우

### 5-1. 복지사 관점 흐름

```
[1] 복지사 로그인 → 자신의 welfare_id 획득
    ↓
[2] 주제 검색 (공공데이터 CSV / TOP10 키워드)
    POST /api/welfare/topics/search
    ↓
[3] AI 질문 생성/수정/편집
    POST /api/welfare/topics/generate-questions
    POST /api/welfare/topics/refine-questions
    POST /api/welfare/topics/save-draft
    ↓
[4] 주제 발행 + 사용자 배포
    POST /api/welfare/topics/publish
    └─ body.welfare_id = 자신의 ID
    └─ body.target_user_ids = [배포할 사용자 ID 목록]
    ↓
[5] DB: weekly_topics 생성 + topic_distributions 생성
    ↓
[6] 사용자 로그인 → 배포된 주제 확인
    GET /api/chat/users/{user_id}/available-surveys
    └─ 내 welfare_id 기준으로 필터링
    ↓
[7] 사용자가 응답 제출
    POST /api/chat/surveys/{topic_id}/respond
    ↓
[8] 복지사가 통계 조회
    GET /api/welfare/surveys/{topic_id}/analytics?welfare_id=자신의ID
    └─ 선택형: 보기별 n명 / 퍼센트
    └─ 서술형: 응답 수 / 샘플 답변
    ↓
[9] 복지사가 배포 현황 확인
    GET /api/welfare/topics/distribution-summary?welfare_id=자신의ID
    └─ 배포 수 / 확인(acknowledged) 수 / 미확인 수
```

### 5-2. 데이터 관계 (ER)

```
welfare_workers (복지사)
     │ 1
     │
     ├──< users (담당 사용자)
     │       │
     │       ├──< survey_responses (사용자 응답)
     │       │
     │       └──< topic_distributions (배포 기록)
     │
     ├──< weekly_topics (발행한 주제)
     │       │
     │       ├──< topic_distributions (이 주제를 누구에게 배포했는지)
     │       └──< survey_responses (이 주제에 대한 응답들)
     │
     └──< survey_templates (저장한 템플릿)
```

### 5-3. 통계 데이터 예시

**선택형 질문 응답 집계** (`GET /api/welfare/surveys/{topic_id}/analytics`):
```json
{
  "topic_id": "...",
  "total_respondents": 3,
  "questions": [
    {
      "question_id": "q1",
      "type": "choice",
      "text": "시장에 가본 적이 있으신가요?",
      "options_stats": [
        {"label": "네, 자주 갔어요", "count": 2, "percent": 66.7},
        {"label": "가끔 갔었어요", "count": 1, "percent": 33.3},
        {"label": "아니오", "count": 0, "percent": 0}
      ]
    },
    {
      "question_id": "q2",
      "type": "narrative",
      "text": "가장 기억에 남는 순간을 이야기해 주세요.",
      "response_count": 3,
      "sample_responses": [
        "어릴 적 어머니 손 잡고...",
        "김치도 사고...",
        "설날에는 항상..."
      ]
    }
  ]
}
```

---

## 6. 수정 작업 리스트

### Phase 1: DB 시드 스크립트 작성

| 파일 | 작업 |
|------|------|
| `backend/seed_accounts.py` | **신규**: 위 시드 데이터를 INSERT하는 스크립트 |
| `backend/check_db.py` | DB 테이블 현황 확인 스크립트 (이미 존재) |

### Phase 2: 백엔드 로그인 API 교체

| 파일 | 작업 |
|------|------|
| `backend/app/routers/auth.py` | `TEMP_ACCOUNTS` 제거, `POST /api/auth/login` 신규 작성 |
| `backend/app/routers/admin.py` | `ADMIN_ID = "admin"` 하드코딩 제거, DB 조회로 변경 |
| `backend/app/routers/__init__.py` (변경 필요 시) | 라우터 등록 확인 |

### Phase 3: 프론트엔드 로그인 화면 교체

| 파일 | 작업 |
|------|------|
| `mobile/screens/LoginScreen.tsx` | 하드코딩 드롭다운 제거, ID/PW 입력 폼 |
| `backend/app/static/login.html` | 하드코딩 `<select>` 제거, ID/PW 입력 폼 |
| `mobile/App.tsx` | 로그인 응답 구조에 맞춰 `welfare_id`도 저장 |

### Phase 4: Dashboard Admin UI (할당 화면)

| 파일 | 작업 |
|------|------|
| `dashboard/src/pages/admin/` | 복지사 할당 UI 드롭다운/버튼 추가 (확인 필요) |

---

## 7. 예상 효과

| 지표 | Before | After |
|------|--------|-------|
| 계정 정보 위치 | auth.py + LoginScreen.tsx + login.html (3곳) | SQLite DB (1곳) |
| 계정 수정 방식 | 3개 파일 동시 수정 | `seed_accounts.py` 재실행 |
| 복지사-사용자 연결 | `LIMIT 1` 자동 연결 (무작위) | DB 시드 시점에 명시적 할당 |
| 로그인 응답 | `{user_id, user_type, nickname}` | `{user_id, user_type, nickname, name, welfare_id}` |
| Admin 식별 | 문자열 `"admin"` | DB 레코드 (`role = 'admin'`) |
| 복지사 격리 | 미적용 (모든 사용자가 섞임) | `welfare_id` 기준 완전 격리 |

---

## 8. 주의사항

1. **기존 DB 데이터 보존**: `seed_accounts.py` 실행 시 기존 `local_ium.db`의 데이터와 충돌하지 않도록 `nickname` 기준 중복 체크
2. **프론트엔드 하위호환**: 기존에 `temp_user_id`, `temp_user_type`을 저장하고 있는 모든 프론트엔드 코드 확인 필요
3. **모바일 AsyncStorage**: `consent_done` 키 등 기존 키 포맷 유지 (새 키 추가만 수행)
4. **데모 계정 필요**: 최초 1회만 실행하면 되도록 시드 스크립트는 멱등성 보장
