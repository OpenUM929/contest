# essays.content_type 컬럼 추가 마이그레이션
# 용도: content_type 컬럼이 없는 기존 DB에 컬럼 추가
# 사용: python _migrate_content_type.py

import asyncio
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

# 로컬 SQLite 모드로 설정 (기본값)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///" + os.path.join(_HERE, "local_ium.db").replace(os.sep, "/"))

from app.database import engine
from sqlalchemy import text


async def migrate():
    async with engine.connect() as conn:
        # SQLite: ALTER TABLE ADD COLUMN (IF NOT EXISTS 미지원 -> 예외 무시)
        if "sqlite" in str(engine.url):
            try:
                await conn.execute(text("ALTER TABLE essays ADD COLUMN content_type VARCHAR(20) DEFAULT 'essay'"))
                await conn.commit()
                print("[Migrate] SQLite: essays.content_type 컬럼 추가 완료")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("[Migrate] SQLite: essays.content_type 컬럼 이미 존재 (건너뜀)")
                else:
                    print(f"[Migrate] SQLite 오류: {e}")
        else:
            # PostgreSQL: ADD COLUMN IF NOT EXISTS
            try:
                await conn.execute(text("ALTER TABLE essays ADD COLUMN IF NOT EXISTS content_type VARCHAR(20) DEFAULT 'essay'"))
                await conn.commit()
                print("[Migrate] PostgreSQL: essays.content_type 컬럼 추가 완료")
            except Exception as e:
                print(f"[Migrate] PostgreSQL 오류: {e}")


if __name__ == "__main__":
    asyncio.run(migrate())
    print("[Migrate] 완료")
