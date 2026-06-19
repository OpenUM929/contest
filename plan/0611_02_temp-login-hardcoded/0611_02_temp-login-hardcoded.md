# 임시 로그인 기능 (하드코딩 프로토타입)

> 상태: DN | 완료일: 2026-06-11
> 작업 유형: 기능 구현 (프로토타입용 임시 로그인)
> 참고 문서: [plan_B_user-chat.md](../../plan/reference/pipeline-B/plan_B_user-chat.md)

---

## 1. 목표

프로토타입 단계에서 하드코딩된 임시 계정으로 빠르게 로그인하고, 관리자가 백엔드에서 계정을 관리할 수 있게 한다.

---

## 2. 구현 내용

### 2-1. 백엔드 — `backend/app/routers/auth.py` (신규)

| 엔드포인트 | 설명 |
|-----------|------|
| `POST /api/auth/temp-login` | `temp_id` → 하드코딩 계정 검증 → DB 자동 생성 → `{user_id, user_type, nickname}` 반환 |
| `GET /api/auth/temp-accounts` | 모든 임시 계정 + DB 매핑 정보 반환 (관리자용) |

**하드코딩된 6개 계정**:
| temp_id | 닉네임 | 유형 |
|---------|--------|------|
| `demo-elder-001` | 김어르신 | elder |
| `demo-elder-002` | 박어르신 | elder |
| `demo-elder-003` | 최어르신 | elder |
| `demo-youth-001` | 김청년 | youth |
| `demo-youth-002` | 이청년 | youth |
| `demo-youth-003` | 박청년 | youth |

### 2-2. 모바일 — `mobile/screens/LoginScreen.tsx` (신규)

- 콤보박스(모달 기반)로 계정 선택
- 그룹 구분: **노인** / **청년**
- "시작하기" 버튼 → API 호출 → AsyncStorage 저장
- `App.tsx`에서 로그인 상태 관리 (AsyncStorage)

### 2-3. 모바일 — `mobile/App.tsx` (수정)

- `DEMO_USER_ID`/`DEMO_USER_TYPE` 하드코딩 제거
- AsyncStorage → 로그인 상태 확인 → LoginScreen / Main 결정
- `onLogout` 콜백 → AsyncStorage 초기화 → LoginScreen으로 복귀

### 2-4. 모바일 — `mobile/screens/ElderlyMain.tsx` / `YouthMain.tsx` (수정)

- "🔄 계정 전환" 버튼 추가
- 클릭 시 Alert 확인 → `onLogout()` 호출

### 2-5. 대시보드 — `dashboard/src/pages/TempAccountPage.tsx` (신규)

- 6개 임시 계정 목록 테이블 표시
- DB 사용자 ID, 마지막 접속일 표시

### 2-6. 대시보드 — `dashboard/src/App.tsx` (수정)

- "🔑 계정 관리" 탭 추가 → TempAccountPage 렌더링

---

## 3. 변경 파일 요약

| 파일 | 변경 | 설명 |
|----------|------|------|
| `backend/app/routers/auth.py` | **신규** | 임시 로그인 API |
| `mobile/screens/LoginScreen.tsx` | **신규** | 콤보박스 로그인 화면 |
| `mobile/App.tsx` | 수정 | 로그인 흐름 통합 |
| `mobile/screens/ElderlyMain.tsx` | 수정 | 계정 전환 버튼 |
| `mobile/screens/YouthMain.tsx` | 수정 | 계정 전환 버튼 |
| `dashboard/src/pages/TempAccountPage.tsx` | **신규** | 관리자 계정 관리 |
| `dashboard/src/App.tsx` | 수정 | 계정 관리 탭 |

---

## 4. 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| 2026-06-11 | 최초 작성 | 임시 로그인 (하드코딩) 기능 구현 완료 |
