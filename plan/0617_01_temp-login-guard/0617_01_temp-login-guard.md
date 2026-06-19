# 로그인 인증 가드(Authentication Guard) 구현 계획

> 상태: DN | 완료일: 2026-06-17

---

## 목차

1. [목표](#1-목표)
2. [현재 문제점](#2-현재-문제점)
3. [해결 방안](#3-해결-방안)
4. [구현 상세](#4-구현-상세)
5. [파일 변경 목록](#5-파일-변경-목록)
6. [테스트 계획](#6-테스트-계획)
7. [수정 이력](#7-수정-이력)

---

## 1. 목표

**로그인(임시 계정 선택)을 거치지 않으면 어떤 페이지든 `/login`으로 강제 리다이렉트**되도록 인증 가드를 구현한다.

- `localStorage`에 `temp_user_id`가 없는 상태로 `/` 또는 다른 정적 페이지에 접근 시 → `/login`으로 이동
- 로그인 성공 후에는 원래 가려던 페이지(또는 타입별 기본 페이지)로 이동
- 이미 로그인된 상태에서 `/login` 접근 시 → `/`로 이동

---

## 2. 현재 문제점

| # | 문제 | 영향 |
|---|------|------|
| 1 | `login.html`이 StaticFiles로 마운트되지 않아 URL(`localhost:8000/login.html`) 접근 불가 | 로그인 페이지 자체를 열 수 없음 |
| 2 | 관리자 대시보드(`/`)에 인증 체크 로직 없음 | 로그인 없이 아묶나 대시보드 진입 가능 |
| 3 | `login.html`과 대시보드(`/`)가 같은 origin에서 서빙되지 않음 | `localStorage` 공유가 원활하지 않을 수 있음 |
| 4 | 노인/청년 로그인 성공 후 `/user.html`로 이동하지만 해당 페이지 **미존재** | 404 오류 발생 |

---

## 3. 해결 방안

### 3-1. 총괄 방침

- **프론트엔드 이중 인증 가드** 방식을 채택한다.
  - 1차: `dashboard/dist/index.html`의 `<script>` (React 로드 전)
  - 2차: `dashboard/src/App.tsx` (React 레벨)
- **백엔드 수정 최소화**: `/login` 엔드포인트만 추가하여 `login.html`을 직접 서빙한다.
- **노인/청년용 사용자 페이지는 미래 작업**으로 분리한다. 현재는 로그인 성공 후 모두 `/`로 이동시키되, `user_type`은 `localStorage`에 저장하여 향후 분기에 활용한다.

### 3-2. 인증 흐름 (After)

```
[브라우저] ──GET /──→ [FastAPI]
              ↓
        StaticFiles (dashboard/dist/index.html)
              ↓
        <script> localStorage.getItem('temp_user_id') ?
              ↓
        없음 → window.location.href = '/login'
              ↓
        있음 → React App 로드
              ↓
        App.tsx에서 다시 체크 → 없으면 /login
              ↓
        Dashboard 렌더링
```

---

## 4. 구현 상세

### 4-1. `ium/backend/app/main.py` 수정

- `login.html` 파일을 읽어 `/login` GET 엔드포인트에서 `HTMLResponse`로 반환한다.
- `login.html` 낸에서 사용하는 정적 자산(CSS, JS 인라인이므로 추가 파일 없음)은 별도 마운트 불필요.

```python
from fastapi.responses import HTMLResponse
import os

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    login_path = os.path.join(os.path.dirname(__file__), "static", "login.html")
    with open(login_path, "r", encoding="utf-8") as f:
        return f.read()
```

### 4-2. `ium/backend/app/static/login.html` 수정

1. **redirect 파라미터 지원**:
   - URL query parameter `?redirect=/some-page`를 읽어 로그인 성공 후 해당 경로로 이동.
   - `redirect` 파라미터가 없으면 `user_type`에 따라 기본 경로로 이동.

2. **로그인 성공 후 이동 로직**:
   - 관리자(`admin`) → `/`
   - 노인/청년(`elder`/`youth`) → `/` (임시 통합, 사용자 페이지 부재)

3. **이미 로그인된 상태 처리**:
   - 페이지 로드 시 `temp_user_id`가 있으면 `/`로 자동 이동.

### 4-3. `ium/dashboard/dist/index.html` 수정

React 앱이 로드되기 전에 실행되는 인증 가드 `<script>`를 `<head>` 최상단에 추가한다.

```html
<script>
  (function() {
    try {
      if (!localStorage.getItem('temp_user_id')) {
        window.location.replace('/login');
      }
    } catch (e) {}
  })();
</script>
```

### 4-4. `ium/dashboard/src/App.tsx` 수정

React 레벨에서도 인증 상태를 체크하여 이중 보호를 구현한다.

```tsx
import { useEffect } from "react";

export default function App() {
  useEffect(() => {
    if (!localStorage.getItem('temp_user_id')) {
      window.location.href = '/login';
    }
  }, []);
  // ...
}
```

추가로 **로그아웃 버튼**을 상단 네비게이션에 배치한다.

```tsx
const handleLogout = () => {
  localStorage.removeItem('temp_user_id');
  localStorage.removeItem('temp_user_type');
  localStorage.removeItem('temp_nickname');
  window.location.href = '/login';
};
```

---

## 5. 파일 변경 목록

| 순서 | 파일 경로 | 변경 유형 | 설명 |
|------|-----------|-----------|------|
| 1 | `ium/backend/app/main.py` | 수정 | `/login` 엔드포인트 추가 |
| 2 | `ium/backend/app/static/login.html` | 수정 | redirect 파라미터 지원, 이동 로직 수정, 이미 로그인 시 리다이렉트 |
| 3 | `ium/dashboard/dist/index.html` | 수정 | `<head>`에 인증 가드 `<script>` 추가 |
| 4 | `ium/dashboard/src/App.tsx` | 수정 | React 레벨 인증 가드 + 로그아웃 버튼 추가 |

---

## 6. 테스트 계획

| # | 시나리오 | 예상 결과 |
|---|---------|----------|
| 1 | 시크릿 모드에서 `localhost:8000/` 접속 | `/login`으로 리다이렉트 |
| 2 | `/login`에서 계정 선택 후 로그인 | `/`로 이동, `localStorage`에 인증 정보 저장 |
| 3 | 로그인된 상태에서 `/` 접속 | 대시보드 정상 표시 |
| 4 | 로그인된 상태에서 `/login` 접속 | `/`로 자동 이동 |
| 5 | 대시보드에서 로그아웃 클릭 | `localStorage` 삭제 후 `/login`으로 이동 |
| 6 | 로그아웃 후 뒤로 가기로 `/` 접근 | `/login`으로 리다이렉트 |

---

## 7. 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| — | — | 최초 작성 |

---

*계획서 저장 위치: `plan/0617_01_temp-login-guard/0617_01_temp-login-guard.md`*
