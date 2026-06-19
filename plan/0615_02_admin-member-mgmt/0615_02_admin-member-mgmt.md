# 관리자 회원 관리 모듈 신규 설계 계획서

> 상태: DONE (Phase 1 구현 완료) | 작성일: 2026-06-15 | 작업 유형: 계획서/설계서

---

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| 2026-06-15 | 최초 작성 | — |
| 2026-06-15 | §2, §4-3, §4-4, §5, §6, §7, §8 | 실증 검증 반영: ① Alembic 미사용 확인 → 마이그레이션을 "로컬 DB 재생성 + `init.sql` 수정" 방식으로 교체 ② 프론트 react-router 미사용 확인 → 기존 탭 패턴 확장 방식으로 교체 ③ 기존 계정 관리 surface(`TempAccountPage`/`auth.py`) 관계 명시 |
| 2026-06-15 | 전체 | **Phase 1 구현 완료.** 백엔드(`models.py`·`init.sql`·`admin.py`·`main.py`), 프론트(`api/admin.ts`·`components/admin/*`·`pages/admin/*`·`App.tsx`) 작성. 통합 스모크 테스트 15/15 통과(BR-001~005 검증), 기존 welfare/auth 회귀 무손상, dashboard 프로덕션 빌드 성공. |

---

## 1. 개요

이음(以音) 프로젝트에서 **관리자가 회원(노인/청년)과 복지사를 등록·수정·삭제·검색·배정할 수 있는 회원 관리 모듈**을 신규 작성합니다.

현재 시스템은 복지사용 대시보드와 모니터링 기능은 있으나, **관리자가 회원을 직접 관리할 수 있는 CRUD 기능이 전무**합니다. 기존 모듈은 하드코딩된 임시 계정과 복지사의 조회-only 기능만 존재하므로, **새로운 관리자 모듈을 처음부터 작성**합니다.

> **기존 계정 surface와의 관계**: `auth.py`의 `TEMP_ACCOUNTS`(하드코딩 데모 계정)와 대시보드의 `TempAccountPage.tsx`("🔑 계정 관리" 탭)가 이미 존재합니다. 이는 **데모 로그인 전용**이며 실제 회원 CRUD가 아닙니다. 본 모듈은 이를 수정/대체하지 않고 **별도 신규 모듈로 추가**합니다. 관리자 식별자는 기존 `auth.py`가 admin 로그인 시 반환하는 `user_id="admin"`과 동일한 `admin_id="admin"` 값을 사용하여 일관성을 유지합니다.

**핵심 원칙**:
- 기존 `welfare.py` / `dashboard`는 절대 수정/삭제하지 않음.
- 새로운 `admin.py` (Backend) + `admin/` pages (Frontend)를 별도로 작성.
- 기존 데이터와 호환성을 유지하며 최소한의 필드만 확장.

---

## 2. 문제 정의 (현재 상태)

### 2-1. DB 레벨

| 항목 | 현재 상태 | 문제 |
|------|-----------|------|
| `User` 모델 | `id, user_type, nickname, is_anonymous, welfare_id, last_seen_at, created_at` | `status`(활성/휴면/탈퇴), `phone`, `email`, `name`(실명), `region`, `note` 필드 부재 |
| `WelfareWorker` 모델 | `id, name, region, email, created_at` | `status`, `phone`, `role`(admin/worker), `note` 필드 부재 |
| 관리자 작업 로그 | 테이블 없음 | 누가, 언제, 무엇을 수정했는지 추적 불가 |

### 2-2. API 레벨

| 필요한 기능 | 현재 존재 여부 | 파일 |
|-------------|--------------|------|
| 회원 등록 | ❌ 없음 | — |
| 회원 목록 (검색+필터+페이징) | ❌ 없음 | — |
| 회원 수정 | ❌ 없음 | — |
| 회원 삭제/탈퇴 | ❌ 없음 | — |
| 복지사 배정/재배정 | ❌ 없음 | — |
| 복지사 등록 | ❌ 없음 | — |
| 복지사 수정 | ❌ 없음 | — |
| 복지사 삭제 | ❌ 없음 | — |
| 관리자 작업 로그 | ❌ 없음 | — |
| 관리자 대시보드 | ❌ 없음 | — |

### 2-3. Frontend 레벨

| 필요한 페이지 | 현재 존재 여부 | 경로 |
|-------------|--------------|------|
| 회원 관리 페이지 | ❌ 없음 | — |
| 복지사 관리 페이지 | ❌ 없음 | — |
| 관리자 작업 로그 페이지 | ❌ 없음 | — |
| 관리자 대시보드 | ❌ 없음 | — |

---

## 3. 목표

### Phase 1 (본 계획)

관리자가 사람을 관리하는 시스템의 **골격(MVP)**을 구축합니다.

1. **회원 관리**: 등록, 목록(검색/필터/페이징), 수정, 삭제(소프트), 복지사 배정
2. **복지사 관리**: 등록, 목록(검색/필터/페이징), 수정, 삭제(보호), 담당 회원 수 확인
3. **관리자 작업 로그**: 관리자의 모든 회원/복지사 수정 이력을 기록 및 조회
4. **관리자 대시보드**: 전체 회원/복지사/미해결 알림 현황, 최근 관리자 활동

### Phase 2~4 (후속 계획)

- Phase 2: 데이터 임포트/익스포트 (CSV), 시스템 설정 관리
- Phase 3: 통계/리포트 (주제별 참여율, 복지사 성과, 이탈률)
- Phase 4: 공지/알림, 이메일 템플릿, 완전 탈퇴(개인정보 삭제)

---

## 4. 설계 상세

### 4-1. DB 모델 확장

#### 4-1-1. `users` 테이블 확장

```python
# 기존 필드는 그대로 유지
status: Mapped[str] = mapped_column(String(20), default="active")
#   - active: 정상
#   - dormant: 휴면 (일정 기간 미접속)
#   - withdrawn: 탈퇴 (소프트 삭제)
phone: Mapped[str | None] = mapped_column(String(20))
email: Mapped[str | None] = mapped_column(String(200))
name: Mapped[str | None] = mapped_column(String(50))      # 실명
region: Mapped[str | None] = mapped_column(String(100))   # 시도/시군구
note: Mapped[str | None] = mapped_column(Text)            # 관리자 메모
updated_at: Mapped[datetime | None] = mapped_column(
    DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
)
```

#### 4-1-2. `welfare_workers` 테이블 확장

```python
# 기존 필드는 그대로 유지
status: Mapped[str] = mapped_column(String(20), default="active")
#   - active: 정상
#   - inactive: 비활성 (퇴사/휴직)
phone: Mapped[str | None] = mapped_column(String(20))
role: Mapped[str] = mapped_column(String(20), default="worker")
#   - admin: 상위 관리자
#   - worker: 현장 복지사
note: Mapped[str | None] = mapped_column(Text)
updated_at: Mapped[datetime | None] = mapped_column(
    DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
)
```

#### 4-1-3. `admin_logs` 테이블 (신규)

```python
class AdminLog(Base):
    __tablename__ = "admin_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    admin_id: Mapped[str] = mapped_column(String(50))
    # 현재는 "admin" (임시). 인증 체계 추가 시 변경.
    action: Mapped[str] = mapped_column(String(50))
    # create_user | update_user | delete_user | assign_worker
    # create_worker | update_worker | delete_worker | ...
    target_type: Mapped[str] = mapped_column(String(20))
    # user | worker
    target_id: Mapped[str] = mapped_column(String(36))
    payload: Mapped[str | None] = mapped_column(Text)
    # JSON 문자열: 변경 전/후 값
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
```

### 4-2. Backend API (`admin.py`)

| Method | Endpoint | 설명 | DTO |
|--------|----------|------|-----|
| `POST` | `/api/admin/users` | 회원 등록 | `UserCreateRequest` |
| `GET` | `/api/admin/users` | 회원 목록 (검색+필터+페이징) | Query params |
| `PATCH` | `/api/admin/users/{user_id}` | 회원 수정 | `UserUpdateRequest` |
| `DELETE` | `/api/admin/users/{user_id}` | 회원 삭제 (소프트) | — |
| `POST` | `/api/admin/users/{user_id}/assign` | 복지사 배정/재배정 | `welfare_id` (body) |
| `POST` | `/api/admin/workers` | 복지사 등록 | `WorkerCreateRequest` |
| `GET` | `/api/admin/workers` | 복지사 목록 (검색+필터+페이징) | Query params |
| `PATCH` | `/api/admin/workers/{welfare_id}` | 복지사 수정 | `WorkerUpdateRequest` |
| `DELETE` | `/api/admin/workers/{welfare_id}` | 복지사 삭제 (보호) | — |
| `GET` | `/api/admin/logs` | 관리자 작업 로그 | Query params |
| `GET` | `/api/admin/dashboard` | 관리자 대시보드 | — |

#### 4-2-1. DTO 상세

**`UserCreateRequest`**
```python
class UserCreateRequest(BaseModel):
    user_type: Literal["elder", "youth"]
    name: str                        # 실명
    nickname: str                    # 서비스 내 표시명
    phone: Optional[str] = None
    email: Optional[str] = None
    region: Optional[str] = None
    welfare_id: Optional[str] = None # 복지사 UUID
    note: Optional[str] = None
```

**`UserUpdateRequest`** (부분 수정)
```python
class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    region: Optional[str] = None
    welfare_id: Optional[str] = None
    status: Optional[Literal["active", "dormant", "withdrawn"]] = None
    note: Optional[str] = None
```

**`WorkerCreateRequest`**
```python
class WorkerCreateRequest(BaseModel):
    name: str
    region: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Literal["admin", "worker"] = "worker"
    note: Optional[str] = None
```

**`WorkerUpdateRequest`** (부분 수정)
```python
class WorkerUpdateRequest(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[Literal["admin", "worker"]] = None
    status: Optional[Literal["active", "inactive"]] = None
    note: Optional[str] = None
```

#### 4-2-2. 핵심 비즈니스 규칙

| 규칙 ID | 설명 |
|---------|------|
| BR-001 | 회원 등록 시 `nickname` 중복 불가. 중복 시 `409 Conflict` 반환. (현재 모델의 `nickname`은 `nullable`이며 DB unique 제약이 없으므로, 중복 검사는 **API 레벨에서** `active`/`dormant` 회원 대상으로 수행. DB 제약은 본 Phase에서 추가하지 않음.) |
| BR-002 | 회원 삭제 시 **소프트 삭제** 적용: `status`를 `withdrawn`으로 변경, `phone`/`email`을 `None`으로 설정, `nickname`을 `[탈퇴] {nickname}`으로 변경. |
| BR-003 | 복지사 삭제 시 **하드 삭제 금지**: `status`를 `inactive`로 변경. 단, 담당 `active` 회원이 1명 이상이면 `409 Conflict` 반환. (재배정 필수) |
| BR-004 | 복지사 배정 시 배정 대상 복지사가 존재하는지(`active`) 확인. |
| BR-005 | 모든 관리자 작업(등록/수정/삭제/배정)은 `AdminLog`에 기록. |
| BR-006 | 인증/보안은 현재 패스. `admin_id`는 `"admin"`으로 고정. (Phase 4에서 JWT/RBAC 연동 예정) |

### 4-3. Frontend 구조

기존 `dashboard` 프로젝트에 관리자 화면을 추가합니다. (별도 프로젝트로 분리하지 않음 — 배포 관리 단순화)

> **⚠️ 라우팅 방식 (검증 반영)**: 현재 `dashboard`는 **react-router를 사용하지 않습니다.** `package.json`에 라우팅 라이브러리가 없고, `App.tsx`는 `useState<Tab>` 기반의 **단순 탭 전환** 구조입니다. 따라서 `/admin/*` URL 라우트를 추가하는 것이 아니라, **기존 탭 패턴을 확장**합니다:
> - `App.tsx`의 `Tab` 타입에 `"admin"` 추가 → 최상단 네비게이션에 "🛠 관리자" 탭 추가
> - admin 탭 내부는 별도의 `useState<AdminTab>`("dashboard" | "users" | "workers" | "logs")로 서브 네비게이션 구성 (`AdminLayout.tsx`)
> - 신규 의존성(react-router) 추가 없음. 기존 아키텍처와 일관성 유지.

#### 4-3-1. 디렉토리 구조

```
ium/dashboard/src/
├── App.tsx                          # Tab 타입에 "admin" 추가 (탭 1개 추가)
├── api/
│   ├── admin.ts                     # /api/admin/* axios 클라이언트
├── pages/
│   ├── Dashboard.tsx                # 기존 (복지사 대시보드) — 그대로
│   ├── TopicManager.tsx             # 기존 — 그대로
│   ├── SurveyManagerPage.tsx        # 기존 — 그대로
│   ├── TempAccountPage.tsx          # 기존 — 그대로
│   └── admin/
│       ├── AdminLayout.tsx          # admin 서브탭 네비게이션 (useState<AdminTab>)
│       ├── AdminDashboard.tsx       # 관리자 메인 대시보드
│       ├── UserManager.tsx          # 회원 관리 (목록, 검색, 등록, 수정, 삭제)
│       ├── WorkerManager.tsx        # 복지사 관리
│       └── AdminLogPage.tsx         # 작업 로그 조회
├── components/
│   └── admin/
│       ├── StatCard.tsx             # 대시보드 통계 카드
│       ├── SearchFilter.tsx         # 공통 검색/필터 컴포넌트
│       ├── DataTable.tsx            # 공통 테이블 (페이징, 정렬)
│       ├── UserFormModal.tsx        # 회원 등록/수정 모달
│       ├── WorkerFormModal.tsx      # 복지사 등록/수정 모달
│       └── ConfirmDialog.tsx        # 삭제 확인 다이얼로그
```

#### 4-3-2. 페이지별 기능

**`AdminDashboard.tsx`**
- 상단 통계 카드 4개: 전체 회원, 노인, 청년, 복지사, 미해결 알림
- 하단: 최근 10건 관리자 작업 로그 요약

**`UserManager.tsx`**
- 검색바: 이름/닉네임/연락처 통합 검색
- 필터: 유형(elder/youth), 상태(active/dormant/withdrawn), 복지사, 지역
- 테이블: 이름, 닉네임, 유형, 상태, 복지사, 지역, 최근 접속, 작업(수정/삭제/배정)
- 페이징: 하단 페이지네이션
- "회원 등록" 버튼 → `UserFormModal` (등록 모드)
- 행 "수정" → `UserFormModal` (수정 모드)
- 행 "삭제" → `ConfirmDialog` → 소프트 삭제 API 호출
- 행 "복지사 배정" → 드롭다운 (복지사 목록) → 즉시 저장

**`WorkerManager.tsx`**
- 검색바: 이름/지역 검색
- 필터: 상태(active/inactive), 역할(admin/worker), 지역
- 테이블: 이름, 지역, 연락처, 역할, 상태, 담당 회원 수, 작업(수정/삭제)
- "복지사 등록" 버튼 → `WorkerFormModal`
- 행 "수정" → `WorkerFormModal`
- 행 "삭제" → `ConfirmDialog` → 삭제 보호 규칙(BR-003) 확인

**`AdminLogPage.tsx`**
- 필터: action, target_type, 기간
- 테이블: 작업 시간, 관리자, 작업 유형, 대상 유형, 대상 ID, 변경 내용
- 페이징

### 4-4. 마이그레이션 계획 (검증 반영 — Alembic 미사용)

> **⚠️ 전제 수정**: `requirements.txt`에 `alembic`이 선언돼 있으나 프로젝트에 `alembic.ini`·`alembic/versions/`가 **존재하지 않으며, 한 번도 초기화된 적이 없습니다.** 스키마는 ① 앱 기동 시 `database.py`의 `create_tables()`(= `Base.metadata.create_all`)와 ② Postgres 컨테이너 최초 기동 시 `init.sql`(docker-compose의 `docker-entrypoint-initdb.d`)로 관리됩니다.
>
> **핵심 제약**: `Base.metadata.create_all`은 **존재하지 않는 테이블만 생성**하며, **기존 테이블에 컬럼을 추가하지 않습니다.** 따라서:
> - 신규 `admin_logs` 테이블 → `create_all`이 **자동 생성** (별도 작업 불필요) ✅
> - 기존 `users`/`welfare_workers`의 **신규 컬럼** → `create_all`로 반영 **안 됨** → 아래 절차 필요 ⚠️

#### 4-4-1. 로컬 (SQLite)

데모 데이터만 존재하므로 **DB 파일 재생성**이 가장 단순하고 안전합니다.

```powershell
# 1) 기존 로컬 DB 삭제 (데모 데이터만 있으므로 손실 무방)
Remove-Item ium/backend/local_ium.db -ErrorAction SilentlyContinue
# 2) 서버 재기동 → create_tables()가 확장된 모델로 전체 테이블 재생성
python ium/backend/run_local.py
```

> 데모 계정/회원은 `auth.py`의 `temp-login` 시 자동 재생성되므로 별도 시드 불필요.

#### 4-4-2. PostgreSQL (Docker)

기존 컨테이너 DB는 컬럼 자동 추가가 안 되므로 둘 중 하나를 적용합니다.

- **방안 A (권장, 운영 데이터 없을 때)**: 볼륨 초기화 후 `init.sql`에 신규 컬럼/`admin_logs` 테이블 DDL을 추가하고 컨테이너 재생성.
  ```bash
  docker-compose down -v   # DB 볼륨 삭제
  docker-compose up -d     # init.sql 재실행 + create_all
  ```
- **방안 B (운영 데이터 보존 필요 시)**: 수동 `ALTER TABLE`로 컬럼만 추가 (데이터 유지).
  ```sql
  ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';
  -- phone, email, name, region, note, updated_at 동일 패턴
  ALTER TABLE welfare_workers ADD COLUMN status VARCHAR(20) DEFAULT 'active';
  -- phone, role(DEFAULT 'worker'), note, updated_at 동일 패턴
  -- admin_logs 는 create_all 이 생성
  ```

> **`init.sql` 동기화 필수**: 방안과 무관하게, 신규 컬럼·`admin_logs` DDL을 `ium/backend/init.sql`에도 반영해야 향후 신규 환경에서 일관됩니다.

#### 4-4-3. 기존 데이터 영향도

- 로컬은 재생성, Postgres는 기본값(`status='active'`, `role='worker'`)이 적용되어 기존 행과 호환됩니다.
- 기존 복지사 대시보드·주제 발행·대화 기능 등 모든 기존 기능에 영향 없음.
- (선택) 정식 Alembic 도입은 Phase 2 이후로 미루며, 본 Phase는 위 절차로 충분합니다.

---

## 5. 파일 구조 및 배치

### 5-1. Backend

```
ium/backend/app/
├── models/
│   └── models.py          # User, WelfareWorker 확장 + AdminLog 추가
├── routers/
│   ├── admin.py           # 신규 (관리자 회원/복지사/로그/대시보드 API)
│   ├── auth.py            # 기존 — 그대로
│   ├── welfare.py         # 기존 — 그대로
│   ├── chat.py            # 기존 — 그대로
│   ├── essay.py           # 기존 — 그대로
│   └── safety.py          # 기존 — 그대로
├── main.py                # admin.py 라우터 등록 추가
└── init.sql               # 신규 컬럼 + admin_logs DDL 반영 (Postgres 신규 환경용)
```

> Alembic 마이그레이션 스크립트는 작성하지 않습니다 (§4-4 참조). 스키마 반영은 로컬 DB 재생성 / Postgres `init.sql`·`ALTER TABLE`로 처리합니다.

### 5-2. Frontend

```
ium/dashboard/src/
├── App.tsx                          # Tab 타입에 "admin" 추가 (탭 1개)
├── api/
│   └── admin.ts
├── pages/
│   └── admin/
│       ├── AdminLayout.tsx          # admin 서브탭 네비게이션
│       ├── AdminDashboard.tsx
│       ├── UserManager.tsx
│       ├── WorkerManager.tsx
│       └── AdminLogPage.tsx
└── components/
    └── admin/
        ├── StatCard.tsx
        ├── SearchFilter.tsx
        ├── DataTable.tsx
        ├── UserFormModal.tsx
        ├── WorkerFormModal.tsx
        └── ConfirmDialog.tsx
```

---

## 6. 구현 단계 (Phase 1)

| 단계 | 작업 | 대상 파일 | 예상 시간 | 의존 |
|------|------|-----------|-----------|------|
| 1 | DB 모델 확장 (`User`, `WelfareWorker`, `AdminLog`) | `models.py` | 30분 | — |
| 2 | 스키마 반영 (로컬 DB 재생성 + `init.sql`에 신규 컬럼/`admin_logs` DDL 추가) | `init.sql`, `local_ium.db` | 40분 | 단계 1 |
| 3 | Admin API 작성 (회원 CRUD + 배정) | `routers/admin.py` | 2시간 | 단계 1 |
| 4 | Admin API 작성 (복지사 CRUD) | `routers/admin.py` | 1시간 | 단계 1 |
| 5 | Admin API 작성 (로그 + 대시보드) | `routers/admin.py` | 1시간 | 단계 1 |
| 6 | `main.py`에 admin 라우터 등록 | `main.py` | 10분 | 단계 3~5 |
| 7 | Frontend API 클라이언트 | `api/admin.ts` | 30분 | 단계 3~5 |
| 8 | 공통 컴포넌트 작성 | `components/admin/` | 1.5시간 | 단계 7 |
| 9 | AdminLayout(서브탭) + AdminDashboard 페이지 | `pages/admin/AdminLayout.tsx`, `AdminDashboard.tsx` | 1.5시간 | 단계 8 |
| 10 | UserManager 페이지 | `pages/admin/UserManager.tsx` | 2시간 | 단계 8 |
| 11 | WorkerManager 페이지 | `pages/admin/WorkerManager.tsx` | 1.5시간 | 단계 8 |
| 12 | AdminLogPage 페이지 | `pages/admin/AdminLogPage.tsx` | 30분 | 단계 8 |
| 13 | `App.tsx`에 "admin" 탭 추가 (탭 패턴 확장, react-router 미사용) | `App.tsx` | 20분 | 단계 9~12 |
| 14 | 통합 테스트 + 기존 대시보드 회귀 확인 | — | 1시간 | 단계 13 |

**총 예상: 약 12.5시간** (Alembic 정식 도입을 생략하고 로컬 재생성/`init.sql` 방식을 택해 마이그레이션 비용을 최소화함)

---

## 7. 체크리스트

### 7-1. 구현 완료 체크리스트

- [ ] DB 모델 확장 (`User.status`, `User.phone`, `User.email`, `User.name`, `User.region`, `User.note`, `User.updated_at`)
- [ ] DB 모델 확장 (`WelfareWorker.status`, `WelfareWorker.phone`, `WelfareWorker.role`, `WelfareWorker.note`, `WelfareWorker.updated_at`)
- [ ] DB 모델 신규 (`AdminLog` 테이블)
- [ ] 스키마 반영: 로컬 `local_ium.db` 재생성 + `init.sql`에 신규 컬럼/`admin_logs` DDL 추가 (Alembic 미사용)
- [ ] Backend API: `POST /api/admin/users` (회원 등록)
- [ ] Backend API: `GET /api/admin/users` (회원 목록, 검색, 필터, 페이징)
- [ ] Backend API: `PATCH /api/admin/users/{id}` (회원 수정)
- [ ] Backend API: `DELETE /api/admin/users/{id}` (회원 소프트 삭제)
- [ ] Backend API: `POST /api/admin/users/{id}/assign` (복지사 배정)
- [ ] Backend API: `POST /api/admin/workers` (복지사 등록)
- [ ] Backend API: `GET /api/admin/workers` (복지사 목록, 검색, 필터, 페이징)
- [ ] Backend API: `PATCH /api/admin/workers/{id}` (복지사 수정)
- [ ] Backend API: `DELETE /api/admin/workers/{id}` (복지사 삭제 보호)
- [ ] Backend API: `GET /api/admin/logs` (작업 로그)
- [ ] Backend API: `GET /api/admin/dashboard` (관리자 대시보드)
- [ ] Backend: `main.py`에 `admin` 라우터 등록
- [ ] Frontend API 클라이언트: `api/admin.ts`
- [ ] Frontend: `components/admin/StatCard.tsx`
- [ ] Frontend: `components/admin/SearchFilter.tsx`
- [ ] Frontend: `components/admin/DataTable.tsx`
- [ ] Frontend: `components/admin/UserFormModal.tsx`
- [ ] Frontend: `components/admin/WorkerFormModal.tsx`
- [ ] Frontend: `components/admin/ConfirmDialog.tsx`
- [ ] Frontend: `pages/admin/AdminLayout.tsx` (admin 서브탭 네비게이션)
- [ ] Frontend: `pages/admin/AdminDashboard.tsx`
- [ ] Frontend: `pages/admin/UserManager.tsx`
- [ ] Frontend: `pages/admin/WorkerManager.tsx`
- [ ] Frontend: `pages/admin/AdminLogPage.tsx`
- [ ] Frontend: `App.tsx`의 `Tab`에 `"admin"` 추가 (탭 패턴 확장, react-router 미도입)
- [ ] 통합 테스트 (회원 등록 → 목록 조회 → 수정 → 삭제 → 로그 확인)
- [ ] 통합 테스트 (복지사 등록 → 회원 배정 → 복지사 삭제 시도)
- [ ] 기존 복지사 대시보드 정상 작동 확인 (회귀 테스트)

### 7-2. 결정 사항 체크리스트

- [x] `User`에 `updated_at` 필드 추가 여부: **추가** (회원 수정 타임스탬프 기록)
- [x] `WelfareWorker`에 `updated_at` 필드 추가 여부: **추가**
- [x] 탈퇴 처리 방식: **소프트 삭제** (`status`를 `withdrawn`으로 변경, 연락처 삭제, 닉네임 prefix 추가)
- [x] 복지사 삭제 시 담당 회원 처리: **삭제 불가** (담당 회원 존재 시 `409` 반환, 재배정 필수)
- [x] 기존 `welfare.py` / dashboard: **절대 수정하지 않음** (새 모듈만 추가)
- [x] 스키마 반영 방식: **Alembic 미사용** → 로컬 DB 재생성 + Postgres `init.sql` 수정/`ALTER TABLE` (프로젝트에 Alembic이 초기화된 적 없음, 데모 데이터뿐이라 가장 단순·안전)
- [x] Frontend 라우팅: **기존 탭 패턴 확장** (`App.tsx`에 `"admin"` 탭 추가 + admin 내부 서브탭) → react-router 신규 도입 안 함 (의존성 최소화, 기존 구조 일관)
- [x] 기존 `TempAccountPage`/`auth.py` 데모 계정: **수정/대체하지 않고 공존** (`admin_id="admin"` 값만 재사용)

---

## 8. 리스크 및 주의사항

| ID | 리스크 | 영향 | 대응 방안 |
|----|--------|------|-----------|
| R-001 | 기존 테이블에 신규 컬럼 미반영 | `create_all`은 기존 테이블에 컬럼을 추가하지 않아, 모델만 바꾸고 DB를 그대로 두면 `no such column` 런타임 오류 발생 | 로컬은 `local_ium.db` **재생성**, Postgres는 `init.sql` 갱신 후 볼륨 초기화(또는 `ALTER TABLE`). 모델 변경과 스키마 반영을 **반드시 동시에** 수행. SQLite/Postgres 양쪽 기동 확인. (§4-4 참조) |
| R-002 | 기존 복지사 대시보드 회귀 | 복지사 기능이 망가짐 | `welfare.py`를 절대 수정하지 않음. `main.py`에 라우터 추가만 수행. 구현 후 기존 대시보드 정상 작동 확인. |
| R-003 | 닉네임 중복 충돌 | 회원 등록 실패 | `UserCreateRequest`에서 `nickname` uniqueness를 API 레벨에서 `409`로 처리. 탈퇴 회원의 닉네임은 `[탈퇴] prefix`로 변경하여 중복 해소. |
| R-004 | 담당 회원 있는 복지사 삭제 | 데이터 무결성 깨짐 | `DELETE /api/admin/workers/{id}`에서 `active` 회원 수를 먼저 확인하고, 0명이 아니면 `409` 반환. |
| R-005 | 인증 부재로 인한 보안 | 누구나 관리자 API 호출 가능 | 현재 패스. Phase 4에서 JWT + RBAC 도입. 지금은 `admin_id="admin"`으로 고정하고 내부망에서만 사용한다는 가정. |
| R-006 | 대량 데이터 페이징 성능 | 회원 1000명 이상 시 느림 | `page_size`를 최대 100으로 제한. `OFFSET` 기반 페이징 적용. 향후 커서 기반 페이징으로 개선 가능. |

---

## 9. 관련 문서

| 문서 | 내용 | 경로 |
|------|------|------|
| 이음 프로젝트 상세 | 작업 유형 분류 | `.clinerules/docs/project/README.md` |
| Plan Mode 규칙 | 계획서 작성/상태/수정 이력 | `.clinerules/core/00-core/03.plan-mode.md` |
| Legacy Protection | 기존 코드 수정 금지 규칙 | `.clinerules/core/01.legacy-protection.md` |
| 백엔드 API 워크플로우 | API 구현 규칙 | `.clinerules/core/03.workflow.md` |
| DB 네이밍 표준 | 테이블/필드 명명 규칙 | `.clinerules/docs/development/database-naming-standard.md` |
| 필드 네이밍 규칙 | 필드명/네이밍 | `.clinerules/docs/development/field-naming-convention.md` |
| 통합 구현 계획 | 전체 파이프라인 설명 | `plan/이음_통합구현계획_20260604.md` |
| 복지사 파이프라인 | 기존 복지사 기능 설명 | `plan/reference/pipeline-F/plan_F_welfare-worker.md` |

---

> **다음 단계**: 사용자가 "수행"을 명시적으로 요청하면, 본 계획서의 Phase 1 구현을 시작합니다.
