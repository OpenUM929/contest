# SQLite 로컬 DB 초기화 스크립트
# SQLAlchemy 모델 기반으로 테이블 자동 생성

import asyncio
import os
import sys

# 로컬 모드 설정
os.environ["ENVIRONMENT"] = "local"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./local_ium.db"
os.environ["SKIP_EMOTION"] = "true"
os.environ["MEDIA_CACHE_DIR"] = "./local_media_cache"
os.makedirs(os.environ["MEDIA_CACHE_DIR"], exist_ok=True)

from app.database import engine, Base
from app.models.models import (
    WelfareWorker, User, WeeklyTopic, Conversation, 
    Essay, SafetyAlert, TopicProposal, SurveyTemplate, SurveyResponse
)

async def init_db():
    """SQLite에 모든 테이블 생성"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("[LocalDB] SQLite 테이블 생성 완료")
    
    # 샘플 복지사 데이터 삽입
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        worker = WelfareWorker(
            name="김복지",
            region="서울 종로구",
            email="welfare1@ium.kr",
        )
        session.add(worker)
        await session.commit()
        print(f"[LocalDB] 샘플 복지사 생성: {worker.name} ({worker.region})")

if __name__ == "__main__":
    asyncio.run(init_db())
    print("[LocalDB] 초기화 완료. 이제 'python run_local.py'로 서버를 시작하세요.")
