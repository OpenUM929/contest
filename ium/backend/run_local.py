# 로컬 개발용 실행 파일
# PostgreSQL 대신 SQLite, Redis 생략, 감정 모델 로딩 생략

import os
import sys
from dotenv import load_dotenv

# .env 파일 로드 (KCISA_API_KEY 등)
load_dotenv()

# 로컬 모드 환경변수 설정
os.environ["ENVIRONMENT"] = "local"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./local_ium.db"
os.environ["SKIP_EMOTION"] = "true"
os.environ["MEDIA_CACHE_DIR"] = "./local_media_cache"

# 미디어 캐시 디렉토리 생성
os.makedirs(os.environ["MEDIA_CACHE_DIR"], exist_ok=True)

# 기존 main.py 실행
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "run_local:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )