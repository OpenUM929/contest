# UUID 타입 불일치 + DB 스키마 불일치 장애 종합 수정 계획서

> 상태: DONE (실제 근본원인 = 상대경로 DB URL, 수정·검증 완료) | 작성일: 2026-06-17 | 작업 유형: 버그 수정

---

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| 2026-06-17 | 최초 작성 | — |
| 2026-06-17 | §2, §3, §4 | 전체 연쇄 장애 분석 추가. 기존 UUID만 쫓던 것을 3가지 근본 원인(DB 스키마/로그인 부재/CORS)으로 확장 |
| 2026-06-17 | §0 (신규) | **실제 근본원인 규명·수정·검증.** `no such column: users.status` 가 계속 재발한 진짜 원인은 "DB를 안 지워서"가 아니라 **DB URL이 상대경로(`./local_ium.db`)** 라서 서버 실행 디렉토리에 따라 서로 다른(낡은) DB 파일을 열었기 때문. 절대경로로 고정 + 중복 DB 파일 제거 후 모든 API 200 확인 |

---

## 0. 실제 근본 원인 (검증 완료 — 이 항목이 결론)

### 0-1. 진짜 원인: 상대경로 DB URL + 중복 DB 파일

`ium/backend/.env` 와 런처(`ium/app.py`, `ium/backend/run_local.py`)가 SQLite 경로를 **상대경로**로 지정했다:

```
# 변경 전
DATABASE_URL=sqlite+aiosqlite:///./local_ium.db        # .env
os.environ["DATABASE_URL"] = "..././backend/local_ium.db"  # app.py
```

SQLAlchemy 는 이 `./` 를 **서버를 띄운 디렉토리(cwd)** 기준으로 해석한다. 그 결과:

| 실행 위치 | 실제 열리는 파일 | 스키마 |
|-----------|------------------|--------|
| `ium/` 에서 `python app.py` | `ium/local_ium.db` | **낡음(7컬럼, status 없음)** ❌ |
| repo 루트에서 `python ium/app.py` | `backend/local_ium.db` | 낡음 ❌ |
| `ium/backend/` 에서 `run_local.py` | `ium/backend/local_ium.db` | 최신(14컬럼) ✅ |

→ 프로젝트에 `local_ium.db` 가 **4개** 생겨 있었고, 0615_02 마이그레이션은 그중 **하나(`ium/backend/`)만** 갱신했다. 서버는 cwd 에 따라 낡은 사본을 열어 `no such column: users.status` 500 을 반복 발생시켰다. "DB를 지우고 재시작" 은 그때 열린 사본 하나만 고치는 **두더지잡기**였을 뿐 재발은 필연이었다.

### 0-2. 적용한 수정 (durable)

1. **DB·미디어 경로를 절대경로로 고정** — 실행 디렉토리와 무관하게 항상 `ium/backend/local_ium.db` 한 파일만 사용.
   - `ium/backend/.env`: `sqlite+aiosqlite:///C:/dev/contest/ium/backend/local_ium.db` (이 파일은 gitignore 되어 머신 고정 절대경로 허용)
   - `ium/app.py`, `ium/backend/run_local.py`: 기본값을 `_BACKEND_DIR` 기준 절대경로로 산출
2. **중복 DB 파일 3개 삭제** — `local_ium.db`, `backend/local_ium.db`, `ium/local_ium.db`(마지막 1개는 구동 중 서버가 점유 → 재시작 시 해제 후 삭제 가능).

### 0-3. 검증 결과 (repo 루트에서 기동 — 과거 실패하던 worst-case)

| 엔드포인트 | 결과 |
|-----------|------|
| `GET /api/admin/users` / `workers` / `dashboard` | **200** ✅ |
| `GET /api/welfare/dashboard` | **200** ✅ |
| `POST/PATCH/DELETE /api/admin/users`·`workers`, `assign` | 전부 **200**, AdminLog 정상 기록 ✅ |

> UUID 타입(`postgresql.UUID(as_uuid=True)`)은 SQLite 에서 generic Uuid 폴백으로 hex 저장되어 정상 동작한다. §3 에서 고친 `str→uuid.UUID` 캐스트와 `admin.py` 의 `_parse_uuid()` 로 쓰기 경로도 모두 통과. 즉 UUID 자체는 추가 수정 불필요했고, **실제 장애는 위 경로 문제였다.**

### 0-4. 사용자가 할 일 (단 하나)

현재 떠 있는 개발 서버를 **재시작**하면 끝. 재시작하면 갱신된 `.env`(절대경로)를 읽어 최신 DB 를 사용하고, 점유 해제된 `ium/local_ium.db` 도 삭제 가능하다.

```powershell
# 어느 디렉토리에서 실행해도 동일한 DB 를 사용함
python ium/app.py --reload
```

---

## 1. 개요

이음(以音) 프로젝트에서 아래 3가지 원인이 연쇄적으로 작용하여 **서버 기동 후 모든 API가 500을 반환**하고, SPA가 로그인 없이 대시보드를 바로 띄우는 장애가 발생했습니다.

---

## 2. 전체 연쇄 장애 분석

### 2-1. 발생 경로 (Chain of Failures)

```
0615_02 관리자모듈에서 User / WelfareWorker 모델 확장
  (status, phone, role, note, updated_at 필드 추가)
    │
    ▼
기존 local_ium.db는 구 스키마 (신규 컬럼 없음)
    │
    ▼
lifespan → create_tables() 실행
  → 하지만 SQLAlchemy의 create_all은 기존 테이블에 컬럼을 추가하지 않음
  → 신규 admin_logs 테이블만 생성됨
    │
    ▼
[1차] 모든 User / WelfareWorker 조회 API 실패
  → "no such column: users.status"
  → "no such column: welfare_workers.status"
  → 500 Internal Server Error
    │
    ├─────────────────────────────────────┐
    ▼                                     ▼
[2차] CORS 헤더 누락              [3차] SPA 로그인 페이지 없음
500 응답에 CORS 헤더가              App.tsx의 초기 탭이
포함되지 않아 브라우저가            "dashboard"로 하드코딩
"No Access-Control-Allow-Origin"   → 인증 여부와 무관하게
오류를 추가로 발생                   바로 Dashboard.tsx 렌더링
    │                                     │
    ▼                                     ▼
최종 사용자 경험:
"http://127.0.0.1:8000/"
→ 빈 화면 또는 깨진 대시보드
→ "Failed to load resource: 500"
→ "No 'Access-Control-Allow-Origin' header"
```

### 2-2. 각 장애의 근본 원인

#### 원인 1: DB 스키마 불일치 (Primary)

| 항목 | 내용 |
|------|------|
| **증상** | `no such column: users.status`, `no such column: welfare_workers.status` |
| **위치** | `ium/backend/local_ium.db` (기존 파일) ↔ `ium/backend/app/models/models.py` (현재 모델) |
| **발생 계기** | `plan/0615_02_admin-member-mgmt`에서 User/WelfareWorker 모델에 `status`, `phone`, `email`, `name`, `region`, `note`, `updated_at`, `role` 필드 추가 |
| **재현율** | 100% (기존 DB를 가진 모든 로컬 환경) |
| **해결** | `local_ium.db` 삭제 후 서버 재시작 (`create_all()`이 최신 스키마로 DB 재생성) |
| **데이터 영향** | 기존 대화/유저 데이터 삭제. 단, `auth.py`의 temp-login이 최초 로그인 시 자동으로 유저 레코드 생성 + `init_local_db.py`로 복지사 시드 가능 |

#### 원인 2: CORS Origin 불일치 (Secondary)

| 항목 | 내용 |
|------|------|
| **증상** | `Access to XMLHttpRequest at 'http://localhost:8000/api/welfare/workers' from origin 'http://127.0.0.1:8000' has been blocked by CORS policy` |
| **위치** | 브라우저: SPA가 `127.0.0.1:8000`에서 로딩, API 요청은 `localhost:8000`으로 전송 |
| **발생 계기** | FastAPI의 `main.py`에서 Dashboard SPA를 `StaticFiles`로 `/`에 마운트 → FastAPI 기본 host인 `127.0.0.1:8000`에서 SPA 서빙. 그러나 프론트 코드의 `VITE_API_URL` 기본값이 `http://localhost:8000` |
| **2차 문제** | 500 응답 시 CORS 미들웨어가 헤더를 추가하지 못함 (500은 예외 처리 경로로, 미들웨어 스택을 거치지 않거나 헤더가 이미 전송된 상태) |
| **해결** | ① `main.py` CORS origins에 `http://127.0.0.1:8000`와 `http://localhost:8000` 모두 명시 (이미 되어 있음) ② **근본 해결**: FastAPI의 CORS 미들웨어가 예외 응답에도 CORS 헤더를 포함하도록 보장. 또는 API base URL을 SPA origin과 동일하게 설정 |

#### 원인 3: 로그인 페이지 부재 (Tertiary)

| 항목 | 내용 |
|------|------|
| **증상** | SPA 첫 로딩 시 로그인 화면 없이 바로 Dashboard 탭 렌더링 |
| **위치** | `ium/dashboard/src/App.tsx` L10: `const [tab, setTab] = useState<Tab>("dashboard")` |
| **발생 계기** | 프로토타입 단계에서 인증 시스템을 생략하고 모든 탭을 즉시 접근 가능하게 설계 |
| **해결** | ① `App.tsx`에 로그인 상태(`isLoggedIn`)를 관리하는 state 추가 ② 미로그인 시 LoginPage 렌더링 ③ LoginPage에서 temp_id를 선택하여 `/api/auth/temp-login` 호출 ④ 성공 응답의 `user_id`를 상위 state에 저장 |

---

## 3. UUID 타입 불일치 (1차 발견 장애)

### 3-1. 증상

```
sqlalchemy.exc.StatementError:
(builtins.AttributeError) 'str' object has no attribute 'hex'
```

### 3-2. 원인

`get_recent_emotions()`, `check_no_contact()`, `trigger_alert()`, `_send_welfare_email()` 함수에서 `user_id`를 `str` 타입으로 받아 UUID 컬럼과 WHERE 비교 시 SQLAlchemy의 `postgresql.UUID(as_uuid=True)` bind processor가 `.hex`를 호출하다 실패.

### 3-3. 수정 완료 (4개 파일)

| 파일 | 변경 사항 |
|------|-----------|
| `app/services/alert.py` | `trigger_alert`, `_send_welfare_email`, `check_no_contact`, `get_recent_emotions`의 `user_id: str` → `user_id: uuid.UUID`. 내부 `uuid.UUID()` 캐스트 제거. `_daily_safety_check_impl`의 `str(user.id)` → `user.id` |
| `app/routers/welfare.py` | `str(user_id)` → `user_id` (L65) |
| `app/routers/safety.py` | 5개 호출부에 `uuid.UUID(user_id)` 래핑 (L20~100) |
| `app/routers/chat.py` | `str(user.id)` → `user.id` (L117) |

---

## 4. 수정 잔여 항목

### 4-1. DB 재생성 (가장 시급)

```
Remove-Item ium/backend/local_ium.db -ErrorAction SilentlyContinue
# 서버 재시작 시 create_all()이 최신 스키마로 DB 생성
```

**영향**: 기존 데모 데이터 삭제. `temp-login` 호출 시 `auth.py`가 자동으로 유저 레코드 생성. `run_local.py` 또는 `init_local_db.py`로 복지사 시드 필요.

### 4-2. 로그인 페이지 추가

```tsx
// App.tsx
const [user, setUser] = useState<{user_id: string, user_type: string, nickname: string} | null>(null);

if (!user) {
  return <LoginPage onLogin={(u) => setUser(u)} />;
}
// 기존 탭 렌더링 ...
```

**필요 파일**:
- `pages/LoginPage.tsx` (신규) — temp_id 목록을 `/api/auth/temp-accounts`에서 불러와 선택 후 `/api/auth/temp-login` 호출
- `App.tsx` 수정 — 로그인 상태 관리

### 4-3. CORS 예외 처리 강화

```python
# main.py - CORS 미들웨어가 모든 응답(500 포함)에 헤더를 추가하도록
# FastAPI의 add_middleware(CORSMiddleware, ...)는 정상 작동 중
# 다만, 예외 핸들러에서도 CORS 헤더를 보장하려면 아래 핸들러 추가 가능
@app.exception_handler(Exception)
async def cors_safe_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        },
    )
```

또는 `VITE_API_URL`을 SPA origin과 동일하게 설정하여 CORS 자체를 회피:
```
# dashboard/.env
VITE_API_URL=http://127.0.0.1:8000
```

---

## 5. 우선순위

| 우선순위 | 작업 | 영향 | 난이도 |
|----------|------|------|--------|
| **P0** | DB 재생성 (`local_ium.db` 삭제) | 모든 API 정상화 | 하 (1분) |
| **P1** | SPA 로그인 페이지 추가 | 사용자 경험 정상화 | 중 (2시간) |
| **P2** | CORS 예외 처리 강화 | 브라우저 에러 로그 제거 | 하 (10분) |

---

## 6. 체크리스트

### 완료
- [x] `alert.py`: 4개 함수 시그니처 변경 (`str` → `uuid.UUID`)
- [x] `welfare.py`: `str(user_id)` 제거
- [x] `safety.py`: 호출부 `uuid.UUID()` 래핑
- [x] `chat.py`: `str(user.id)` 제거

### 잔여
- [ ] `local_ium.db` 삭제 및 서버 재시작
- [ ] `GET /api/welfare/dashboard` 200 확인
- [ ] `GET /api/safety/check/{uuid}` 200 확인
- [ ] `POST /api/chat` 위기 키워드 테스트
- [ ] `LoginPage.tsx` 신규 작성
- [ ] `App.tsx` 로그인 상태 관리 추가
- [ ] CORS 예외 핸들러 추가 또는 `VITE_API_URL` 통일

---

## 7. 관련 문서

| 문서 | 내용 | 경로 |
|------|------|------|
| 관리자 회원 관리 모듈 계획 | DB 모델 확장 내역 | `plan/0615_02_admin-member-mgmt/0615_02_admin-member-mgmt.md` |
| 통합 구현 계획 | 전체 파이프라인 설명 | `plan/이음_통합구현계획_20260604.md` |

---

> **현재 상태**: UUID 수정 완료. DB 재생성 + 로그인 페이지 + CORS는 미적용.
