# 이음(以音) — 빠른 시작 가이드

## 사전 준비

- Docker Desktop 설치
- `.env` 파일 생성 (`.env.example` 참고)

```
cp .env.example .env
# .env 파일을 열어 API 키 입력
```

## Phase 1 실행 (백엔드 + DB)

```bash
docker-compose up -d
```

서버 확인:
```bash
curl http://localhost:8000/health
# {"status":"ok","service":"이음(以音)"}
```

## API 테스트 순서

### 1. 사용자 등록
```bash
curl -X POST http://localhost:8000/chat/users \
  -H "Content-Type: application/json" \
  -d '{"user_type": "elder", "nickname": "이순자 어르신"}'
```

### 2. 이번 주 주제 확인
```bash
curl http://localhost:8000/chat/topic
```

### 3. 대화하기
```bash
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<위에서 받은 user_id>", "message": "남대문 시장 생각나네요"}'
```

### 4. 수필 생성 (5건 이상 대화 후)
```bash
curl -X POST http://localhost:8000/essay/generate
```

### 5. 복지사 대시보드
```bash
curl http://localhost:8000/welfare/dashboard
```

### 6. 안전 점검
```bash
curl http://localhost:8000/safety/check/<user_id>
```

## Swagger UI

```
http://localhost:8000/docs
```

## 모바일 앱 실행

```bash
cd mobile
npm install
npx expo start
```

## 복지사 대시보드 실행

```bash
cd dashboard
npm install
npm run dev
# http://localhost:5173
```

## Phase 3 전환 (국내 AI)

`.env`에 Clova 키를 추가하면 자동 전환:
```
CLOVA_CLIENT_ID=your_clova_id
CLOVA_CLIENT_SECRET=your_clova_secret
```
