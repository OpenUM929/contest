# 01 — 프로젝트 스캔 전략

## 언어/프레임워크 감지 순서

```bash
# 1. 루트 파일 목록
ls -la

# 2. 주요 설정 파일 읽기 (해당하는 것만)
cat package.json          # Node.js / JS / TS
cat pyproject.toml        # Python (Poetry/PDM)
cat requirements.txt      # Python (pip)
cat Cargo.toml            # Rust
cat go.mod                # Go
cat pom.xml               # Java (Maven)
cat build.gradle          # Java/Kotlin (Gradle)

# 3. 폴더 구조 파악 (3단계 깊이까지)
find . -type d \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/dist/*' \
  -not -path '*/build/*' \
  | sort
```

## 프레임워크별 핵심 파악 포인트

### Next.js / React
```
파악 필수:
- app/ 또는 pages/ 구조 (라우팅 방식)
- components/ 분류 방식 (atomic, feature-based 등)
- lib/ 또는 utils/ 역할 구분
- API routes 위치
- 상태관리 라이브러리 (zustand, redux 등)
```

### FastAPI / Django / Flask
```
파악 필수:
- routers/ 또는 views/ 구조
- models/ (ORM 모델)
- schemas/ 또는 serializers/ (입출력 스키마)
- services/ 또는 crud/ (비즈니스 로직)
- 미들웨어 위치
- DB 마이그레이션 구조
```

### NestJS
```
파악 필수:
- 모듈 분리 단위 (feature module 패턴)
- controllers / services / repositories 레이어
- 공통 모듈 (auth, common, shared)
- DTOs 위치
```

### 공통 파악 항목
```
- 환경변수 파일 (.env.example, .env.local)
- 테스트 구조 (unit, integration, e2e 분리 여부)
- CI/CD 파일 (.github/workflows, .gitlab-ci.yml)
- 도커 파일 (Dockerfile, docker-compose.yml)
- 린트/포매터 설정 (.eslintrc, .prettierrc, ruff.toml)
```

## 진입점 파일 찾기

```bash
# JS/TS 진입점
cat package.json | grep -E '"main"|"scripts"'

# Python 진입점
find . -name "main.py" -o -name "app.py" -o -name "__main__.py" \
  | grep -v node_modules

# 실행 스크립트
cat Makefile 2>/dev/null || cat justfile 2>/dev/null
```

## 스캔 결과 정리 형식

스캔 후 내부적으로 다음 형식으로 정리 후 Step 2로 진행:

```
[언어] TypeScript
[프레임워크] Next.js 14 (App Router)
[패키지매니저] pnpm
[주요폴더] app/, components/, lib/, public/, tests/
[진입점] app/layout.tsx, app/page.tsx
[상태관리] Zustand (lib/store/)
[API] app/api/ (Route Handlers)
[테스트] Jest + Testing Library (tests/)
[배포] Vercel (vercel.json)
[환경변수] .env.local.example 참조