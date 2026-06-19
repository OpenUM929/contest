# 복지사 계정 관리 기능 개선 계획서

> 상태: DN | 작성일: 2026-06-17 | 작업 유형: 계획서/설계서

---

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| — | — | 최초 작성 |
| 2026-06-17 | §3-1-2, §3-3-1, §3-4-2, §3-4-3, §5 | 검토 피드백 반영: 시드 데이터 보완, Step 3 조회 시점 명시, 모달 UI 단순 체크박스 확정, Phase 2 계획 추가, 리스크 보강 |

---

## 목차

1. [목표](#1-목표)
2. [현재 문제점](#2-현재-문제점)
3. [변경 사항별 상세](#3-변경-사항별-상세)
4. [파일 변경 목록](#4-파일-변경-목록)
5. [구현 단계](#5-구현-단계)
6. [체크리스트](#6-체크리스트)
7. [리스크 및 주의사항](#7-리스크-및-주의사항)

---

## 1. 목표

이음(以音) 프로젝트에서 다음 4가지 기능 개선을 수행합니다:

1. **새 주제 발행 시 배포 대상 선정**: 복지사가 배포할 사용자를 직접 선택 가능
2. **계정 관리 유형 버그 수정**: 관리자 유형이 "청년"으로 표시되는 문제 수정
3. **복지사 임시 계정 정보 추가**: 로그인 화면 및 임시 계정 관리에 복지사 계정 추가
4. **복지사-회원 할당 기능**: 관리자가 복지사에게 담당 노인/청년을 배정/해제 가능

---

## 2. 현재 문제점

### 2-1. 새 주제 발행 시 배포 대상 자동 선정

| 항목 | 현재 상태 | 문제 |
|------|-----------|------|
| `POST /api/welfare/topics/publish` | `welfare_id`에 연결된 모든 사용자에게 자동 `TopicDistribution` 생성 | 복지사가 배포 대상을 선정할 수 없음 |
| `TopicManager.tsx` Step 3 | 발행 확인 후 "📬 배포 대상 (N명)"만 표시 | 발행 전 배포 대상을 선택하는 UI 없음 |

### 2-2. 계정 관리 유형 표시 버그

| 항목 | 현재 상태 | 문제 |
|------|-----------|------|
| `TempAccountPage.tsx` | `user_type === "elder"` → "노인", `else` → "청년" | 관리자(admin)도 "청년"으로 표시 |

### 2-3. 복지사 임시 계정 부재

| 항목 | 현재 상태 | 문제 |
|------|-----------|------|
| `auth.py`의 `TEMP_ACCOUNTS` | admin 1 + elder 3 + youth 3 = 7개 | 복지사 계정 없음 |
| `login.html` | optgroup: 관리자, 노인, 청년 | 복지사 optgroup 없음 |
| `TempAccountPage.tsx` | admin/elder/youth 유형만 표시 | worker 유형 렌더링 불가 |

### 2-4. 복지사-회원 할당 UI 부재

| 항목 | 현재 상태 | 문제 |
|------|-----------|------|
| `admin.py` | `/api/admin/users/{user_id}/assign` 존재 | 복지사 기준 일괄 할당 API 없음 |
| `UserManager.tsx` | 개별 회원의 복지사 드롭다운 변경으로 배정 가능 | 복지사 기준 관리자 시점의 할당 UI 없음 |
| `WorkerManager.tsx` | 복지사 CRUD만 가능 | 담당 회원 관리 UI 없음 |

---

## 3. 변경 사항별 상세

### 3-1. 새 주제 발행 — 배포 대상 직접 선택

#### 3-1-1. Backend (`welfare.py`)

**`TopicPublishRequest`**에 `target_user_ids` 필드 추가:
```python
class TopicPublishRequest(BaseModel):
    # ... 기존 필드 유지 ...
    target_user_ids: list[str] | None = None  # 선택한 사용자 ID 목록 (신규)
```

**`publish_topic`** 함수 수정:
- `target_user_ids`가 제공되면 → 해당 ID 목록의 사용자에게만 `TopicDistribution` 생성
- `target_user_ids`가 `None`이거나 빈 배열이면 → 배포 없이 주제만 발행 (기존 동작과 차별화)
- 복지사 관할 여부 검증: `target_user_ids`의 모든 ID가 해당 복지사의 관할 사용자인지 확인

#### 3-1-2. Frontend (`TopicManager.tsx`)

Step 3(발행 확인) 단계에서 **배포 대상 선택 UI** 추가:
- **Step 3 진입 시점**에 `GET /api/welfare/workers/{welfare_id}/users`로 관할 사용자 목록 조회
  - (Step 1에서 이미 복지사가 선택되어 있으므로, Step 3 진입 시에만 호출. Step 3 내에서는 복지사 변경 불가)
- 사용자 목록을 체크박스로 표시 (닉네임 + 유형 태그: 노인/청년)
- **전체 선택** / **전체 해제** 버튼
- 선택한 사용자 ID를 `target_user_ids`로 담아 발행 API 호출
- 발행 시점에 선택된 사용자가 없으면 경고 메시지 표시 후 진행 가능 ("배포 없이 주제만 발행됩니다")
- 위치: Step 3의 "질문 유형" 아래, "발행" 버튼 위

**기본 상태**: 모두 미선택 (복지사가 반드시 직접 체크)

---

### 3-2. 계정 관리 유형 표시 버그 수정

#### 3-2-1. Frontend (`TempAccountPage.tsx`)

유형 표시 로직을 세분화:
```typescript
{/* Badge mapping */}
{a.user_type === "admin" && <관리자 배지>}
{a.user_type === "elder" && <노인 배지 (기존 스타일)>}
{a.user_type === "youth" && <청년 배지 (기존 스타일)>}
{a.user_type === "worker" && <복지사 배지 (신규)>}
```

**배지 스타일**:
| 유형 | 배경색 | 글자색 |
|------|--------|--------|
| `admin` | `#E8E0D8` | `#6B4C2A` |
| `elder` | `#FFF0E0` | `#E8572A` |
| `youth` | `#E0E0FF` | `#7B7BFF` |
| `worker` | `#D4EDDA` | `#155724` |

---

### 3-3. 복지사 임시 계정 추가

#### 3-3-1. Backend (`auth.py`)

**`TEMP_ACCOUNTS`**에 복지사 계정 추가:
```python
"demo-worker-001": {"user_type": "worker", "nickname": "김복지"},
```

**`temp_login`** 함수에 `worker` 유형 처리 추가:
- `user_type == "worker"`인 경우: `WelfareWorker` 테이블에서 `name`으로 조회
- 존재하면 해당 복지사의 `id`를 `user_id`로, `name`을 `nickname`으로 반환
- 존재하지 않으면 `HTTPException(404, "복지사 계정을 찾을 수 없습니다.")` 반환
- 기존 `User` 테이블 생성 로직은 건너뛰고, 복지사 전용 반환값 구성

**반환값 예시**:
```json
{
  "user_id": "<welfare_worker_id>",
  "user_type": "worker",
  "nickname": "김복지"
}
```

> **설계 이유**: 복지사는 `WelfareWorker` 테이블에 존재하는 별도 엔티티입니다. `User` 테이블에 생성하지 않고, `WelfareWorker`의 ID와 이름을 직접 반환합니다. 대시보드(`App.tsx`)는 `localStorage`의 `temp_user_type`을 확인하지 않고 모든 탭을 보여주므로, 복지사도 모든 기능(대시보드/주제관리/설문지)에 접근 가능합니다.

**시드 데이터 주의사항**:
- `auth.py`의 `temp_login`에서 `WelfareWorker.name == "김복지"`를 조회하므로, **DB에 `김복지` 복지사가 미리 존재해야 합니다**.
- `init_local_db.py`에 `김복지` 복지사 시드 데이터를 추가해야 합니다. (없을 경우 로그인 시 404)
- `init_local_db.py` 확인 결과 `김복지` 복지사가 이미 시드되어 있으면 추가 작업 불필요.

#### 3-3-2. Frontend (`login.html`)

복지사 optgroup 추가:
```html
<optgroup label="👥 복지사">
  <option value="demo-worker-001">김복지</option>
</optgroup>
```

#### 3-3-3. Frontend (`TempAccountPage.tsx`)

- "6개의 임시 계정" 안내문을 "7개의 임시 계정"으로 수정 (또는 동적 표시)
- 복지사 계정의 유형 배지 스타일 적용 (§3-2-1 참조)

---

### 3-4. 복지사-회원 할당 기능

#### 3-4-1. Backend (`admin.py`)

**신규 API 추가**:

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET` | `/api/admin/workers/{welfare_id}/users` | 특정 복지사에 배정된 회원 목록 (pagination) |
| `POST` | `/api/admin/workers/{welfare_id}/assign` | 복지사에 회원 일괄 배정 (body: `{ user_ids: string[] }`) |
| `POST` | `/api/admin/workers/{welfare_id}/unassign` | 복지사에서 회원 일괄 해제 (body: `{ user_ids: string[] }`) |

**`POST /api/admin/workers/{welfare_id}/assign`** 상세:
```python
class BulkAssignRequest(BaseModel):
    user_ids: list[str]

@router.post("/workers/{welfare_id}/assign")
async def bulk_assign_worker(welfare_id: str, body: BulkAssignRequest, db):
    # 1. 복지사 존재 및 active 확인
    # 2. user_ids의 모든 사용자 존재 확인
    # 3. 각 사용자의 welfare_id를 해당 복지사로 설정
    # 4. AdminLog 기록
```

기존 `POST /api/admin/users/{user_id}/assign`은 개별 배정용으로 유지됩니다.

#### 3-4-2. Frontend (`WorkerManager.tsx`)

**"담당 회원 관리" 버튼** 추가:
- 각 복지사 행의 "작업" 컬럼에 버튼 추가
- 클릭 시 모달 열림

**모달 UI (단순 체크박스 방식 — 확정)**:
```
┌──────────────────────────────────────────┐
│  💼 {복지사명} 담당 회원 관리             │
│                                          │
│  전체 선택 | 전체 해제                    │
│                                          │
│  [☐] 회원A (노인)   │ 지역: 서울       │
│  [☑] 회원B (청년)   │ 지역: 부산       │
│  [☐] 회원C (노인)   │ 지역: 대전       │
│  [☑] 회원D (청년)   │ 지역: 서울       │
│  ...                                    │
│                                          │
│  ※ 체크 = 담당으로 배정                   │
│  ※ 체크 해제 = 담당 해제                  │
│                                          │
│        [저장]              [취소]         │
└──────────────────────────────────────────┘
```

**데이터 흐름**:
1. 모달 열기 → 두 API 병렬 호출:
   - `GET /api/admin/workers/{welfare_id}/users` → 현재 담당 회원 목록 (welfare_id 기준 조회)
   - `GET /api/admin/users?status=active&page_size=999` → 전체 active 회원 목록
2. 전체 회원 목록을 하나의 체크박스 리스트로 표시
   - **체크됨** = 현재 해당 복지사의 담당 회원인 상태
   - **체크 해제** = 미배정 또는 다른 복지사 담당
3. 저장 버튼 클릭 시 차분(Diff) 방식으로 assign/unassign API 호출:
   - 기존 담당 목록과 새 체크 상태를 비교
   - 새로 체크된 회원 → `POST /api/admin/workers/{welfare_id}/assign`
   - 체크 해제된 회원 → `POST /api/admin/workers/{welfare_id}/unassign`
4. 저장 후: `load(page)`로 복지사 테이블 갱신 (담당 회원 수 업데이트)

**참고**: 이미 다른 복지사에 배정된 회원을 체크하면 자동으로 재배정됩니다. (`assign` API가 `welfare_id`를 덮어씀)

#### 3-4-3. Phase 2 계획 (본 작업 범위 밖)

향후 확장이 필요한 항목:
- **데이터 임포트/익스포트**: CSV로 복지사-회원 할당 관계 일괄 등록
- **할당 이력 조회**: 복지사별 배정 변경 이력 (AdminLog 활용)
- **알림**: 회원 배정/재배정 시 복지사에게 이메일/알림 발송
- **권한 연동**: Phase 4 JWT/RBAC와 복지사 role(admin/worker) 연동하여 할당 권한 제어

---

## 4. 파일 변경 목록

### 4-1. Backend

| 순서 | 파일 경로 | 변경 유형 | 설명 |
|------|-----------|-----------|------|
| 0 | `ium/backend/init_local_db.py` | 확인/수정 | `김복지` 복지사 시드 데이터 확인 및 추가 (필요 시) |
| 1 | `ium/backend/app/routers/welfare.py` | 수정 | `TopicPublishRequest`에 `target_user_ids` 추가, `publish_topic`에서 조건부 배포 |
| 2 | `ium/backend/app/routers/auth.py` | 수정 | `TEMP_ACCOUNTS`에 `demo-worker-001` 추가, `temp_login`에 `worker` 처리 로직 추가 |
| 3 | `ium/backend/app/routers/admin.py` | 수정 | 복지사 기준 배정/해제 API 3개 추가 |

### 4-2. Frontend (Dashboard)

| 순서 | 파일 경로 | 변경 유형 | 설명 |
|------|-----------|-----------|------|
| 1 | `ium/dashboard/src/pages/TopicManager.tsx` | 수정 | Step 3에 배포 대상 체크박스 UI 추가 |
| 2 | `ium/dashboard/src/pages/TempAccountPage.tsx` | 수정 | user_type별 배지 세분화 (admin/worker 추가) |
| 3 | `ium/dashboard/src/pages/admin/WorkerManager.tsx` | 수정 | "담당 회원 관리" 버튼 + 모달 추가 |
| 4 | `ium/backend/app/static/login.html` | 수정 | 복지사 optgroup 추가 |

---

## 5. 구현 단계

| 단계 | 작업 | 대상 파일 | 예상 시간 |
|------|------|-----------|-----------|
| 1 | `init_local_db.py` 확인 및 `김복지` 복지사 시드 데이터 추가 (없는 경우) | `init_local_db.py` | 10분 |
| 2 | 복지사 임시 계정 추가 (Backend) | `auth.py` | 20분 |
| 3 | 로그인 페이지에 복지사 추가 | `login.html` | 10분 |
| 4 | 계정 관리 유형 버그 수정 | `TempAccountPage.tsx` | 15분 |
| 5 | `TopicPublishRequest`에 `target_user_ids` 추가 + `publish_topic` 조건부 배포 | `welfare.py` | 40분 |
| 6 | 배포 대상 선택 UI (TopicManager Step 3) | `TopicManager.tsx` | 1시간 |
| 7 | 복지사-회원 할당 Backend API 3개 추가 | `admin.py` | 30분 |
| 8 | 담당 회원 관리 모달 UI (WorkerManager) | `WorkerManager.tsx` | 1시간 |
| 9 | 통합 테스트 및 회귀 확인 | — | 30분 |

**총 예상: 약 3.5시간**

---

## 6. 체크리스트

### 6-1. 구현 체크리스트

- [ ] `init_local_db.py`: `김복지` 복지사 시드 데이터 확인 및 추가 (필요 시)
- [ ] `auth.py`: `TEMP_ACCOUNTS`에 `demo-worker-001` 추가
- [ ] `auth.py`: `temp_login`에 `user_type == "worker"` 처리 로직
- [ ] `login.html`: 복지사 optgroup 추가
- [ ] `TempAccountPage.tsx`: admin/worker 유형 배지 추가
- [ ] `welfare.py`: `TopicPublishRequest`에 `target_user_ids` 필드 추가
- [ ] `welfare.py`: `publish_topic` 조건부 배포 로직 + 관할 검증
- [ ] `TopicManager.tsx`: Step 3 배포 대상 체크박스 UI (목록 조회 + 선택)
- [ ] `admin.py`: `GET /api/admin/workers/{welfare_id}/users` (배정된 회원 목록)
- [ ] `admin.py`: `POST /api/admin/workers/{welfare_id}/assign` (일괄 배정)
- [ ] `admin.py`: `POST /api/admin/workers/{welfare_id}/unassign` (일괄 해제)
- [ ] `WorkerManager.tsx`: "담당 회원 관리" 버튼
- [ ] `WorkerManager.tsx`: 담당 회원 할당 모달 UI (체크박스 + diff 저장)

### 6-2. 테스트 체크리스트

- [ ] 복지사 임시 계정 로그인 정상 작동
- [ ] 계정 관리 페이지에서 모든 유형(admin/elder/youth/worker) 올바르게 표시
- [ ] 주제 발행 시 배포 대상 선택 가능
- [ ] 선택한 사용자에게만 배포됨
- [ ] 배포 대상 미선택 시 배포 없이 주제만 발행
- [ ] 복지사 담당 회원 할당/해제 정상 작동
- [ ] 할당 후 복지사 담당 회원 수 업데이트
- [ ] 기존 발행/대시보드 기능 회귀 없음

---

## 7. 리스크 및 주의사항

| ID | 리스크 | 영향 | 대응 방안 |
|----|--------|------|-----------|
| R-001 | 복지사 로그인 시 `WelfareWorker` 미존재 | 로그인 실패 | `temp_login`에서 `WelfareWorker` 부재 시 명확한 404 반환 + 시드 데이터 사전 확인 |
| R-002 | `target_user_ids`가 선택된 복지사 관할 사용자가 아닌 경우 | 무결성 위반 | `publish_topic`에서 각 user_id가 해당 welfare_id의 관할인지 검증 |
| R-003 | 기존 `welfare.py`의 `publish_topic` 호환성 | 기존 API 호출 실패 | `target_user_ids`를 `None` 허용 (optional), `None`이면 기존 동작 유지. **단, Frontend는 항상 target_user_ids를 전송하므로 실제로는 None 케이스 없음** |
| R-004 | 복지사-회원 할당 시 동시성 | 두 관리자가 동시에 할당 시 충돌 | 마지막 저장 기준 적용 (의도적. Phase 4에서 트랜잭션 락 도입 검토) |
| R-005 | `GET /api/welfare/workers/{welfare_id}/users`와 `GET /api/admin/workers/{welfare_id}/users` 중복 | 유지보수 비용 증가 | admin.py의 API는 admin prefix 하에서만 동작하므로 명시적 분리. 향후 통합 검토 가능 |

---

*계획서 저장 위치: `plan/0617_02_welfare-features/0617_02_welfare-features.md`*
