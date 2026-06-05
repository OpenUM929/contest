# 프로젝트 정리 보고서

> 작성일: 2026-06-05
> 정리 대상: contest 저장소 불필요 파일 제거 및 `.gitignore` 적용

---

## 1. 정리 개요

기존 저장소에 커밋되어 있던 불필요한 파일/디렉토리를 제거하고,  
앞으로 동일한 파일들이 다시 커밋되지 않도록 `.gitignore`를 추가했습니다.

---

## 2. 삭제한 파일/디렉토리 목록

| 분류 | 파일/디렉토리 | 삭제 사유 |
|------|-------------|-----------|
| 의존성 | `ium/dashboard/node_modules/` | npm 패키지 (재설치 가능) |
| 가상환경 | `ium/backend/venv/` | Python 가상환경 |
| 가상환경 | `ium/backend/venv-test/` | Python 테스트 가상환경 |
| 민감정보 | `ium/backend/.env` | API 키/비밀번호 등 |
| 로그 | `ium/backend/server.log` | 서버 로그 |
| 로그 | `ium/backend/server_err.log` | 서버 에러 로그 |
| 로그 | `ium/dashboard/dev.log` | 개발 로그 |
| 로그 | `ium/dashboard/preview.log` | 프리뷰 로그 |
| 로그 | `err.txt` | 에러 로그 |
| 로그 | `server_out.txt` | 서버 출력 로그 |
| 로그 | `server_err2.txt` | 서버 에러 로그 2 |
| 임시 디렉토리 | `.vite/` | Vite 캐시 |
| 임시 디렉토리 | `.claude/` | Claude 설정 캐시 |
| 빌드 출력물 | `ium/dashboard/dist/` | 빌드 결과물 |
| 데이터베이스 | `ium/backend/local_ium.db` | 로컬 SQLite DB |
| 캐시 | `ium/backend/local_media_cache/` | 미디어 캐시 |
| 테스트 출력 | `ium/backend/search_empty.json` | 테스트 임시 결과 |
| 테스트 출력 | `ium/backend/search_empty2.json` | 테스트 임시 결과 |
| 테스트 출력 | `ium/backend/search_test.json` | 테스트 임시 결과 |
| 테스트 출력 | `ium/backend/gen_test.json` | 테스트 임시 결과 |
| Python 캐시 | `__pycache__/` (전체) | Python 바이트코드 캐시 |

---

## 3. 추가한 파일

| 파일 | 목적 |
|------|------|
| `.gitignore` | 위 불필요 파일들이 Git 추적 대상에서 제외되도록 설정 |

---

## 4. 개발 환경 복원 방법

정리 후 로컬에서 개발 환경을 다시 구성하려면 다음 단계를 따르세요.

### 4.1 Backend (Python)

```bash
cd ium/backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env.example 참고)
copy .env.example .env
# .env 파일을 열어 실제 API 키/값 입력
```

### 4.2 Dashboard (Node.js)

```bash
cd ium/dashboard

# 패키지 설치
npm install

# 개발 서버 실행
npm run dev
```

### 4.3 Mobile

```bash
cd ium/mobile

# 패키지 설치
npm install
```

---

## 5. 현재 프로젝트 구조 (정리 후)

```
contest/
├── .gitignore
├── README.md
├── ium/
│   ├── README.md
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── init.sql
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   ├── init_local_db.py
│   │   ├── run_local.py
│   │   └── ... (테스트 스크립트)
│   ├── dashboard/
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── main.tsx
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── api/
│   │   │   └── types/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   └── index.html
│   ├── mobile/
│   │   ├── components/
│   │   ├── screens/
│   │   ├── api/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── package.json
│   └── docs/
├── doc/
├── plan/
└── 이음_* (구현계획/가이드 문서)
```

---

## 6. 참고사항

- `node_modules/`나 `venv/`는 `.gitignore`에 의해 추척되지 않으므로,  
  새로 클론한 후 반드시 `npm install` 또는 `pip install -r requirements.txt`를 실행해야 합니다.
- `.env` 파일 역시 Git에 포함되지 않으므로, 팀원 간 공유는 별도 보안 채널을 이용하세요.
