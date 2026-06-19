import asyncio
import hashlib
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal, create_tables
from app.models.models import WelfareWorker, User


SEED_WORKERS = [
    {
        "id": uuid.UUID("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"),
        "name": "관리자",
        "email": "admin@ium.kr",
        "phone": "010-0000-0000",
        "password": "admin1234",
        "role": "admin",
        "region": "서울특별시",
    },
    {
        "id": uuid.UUID("b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e"),
        "name": "김복지",
        "email": "kim@welfare.kr",
        "phone": "010-1000-0001",
        "password": "demo1234",
        "role": "worker",
        "region": "서울 종로구",
    },
    {
        "id": uuid.UUID("c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f"),
        "name": "이복지",
        "email": "lee@welfare.kr",
        "phone": "010-1000-0002",
        "password": "demo1234",
        "role": "worker",
        "region": "경기 수원시",
    },
]

SEED_USERS = [
    {"id": uuid.UUID("d1000000-0000-4000-a000-000000000001"), "user_type": "elder", "name": "김길동",  "nickname": "김어르신", "email": "elder1@test.kr",  "phone": "010-1111-0001", "welfare_id": uuid.UUID("b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e"), "password": "demo1234"},
    {"id": uuid.UUID("d1000000-0000-4000-a000-000000000002"), "user_type": "elder", "name": "박말순",  "nickname": "박어르신", "email": "elder2@test.kr",  "phone": "010-1111-0002", "welfare_id": uuid.UUID("b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e"), "password": "demo1234"},
    {"id": uuid.UUID("d1000000-0000-4000-a000-000000000003"), "user_type": "youth", "name": "최민수",  "nickname": "김청년",   "email": "youth1@test.kr",  "phone": "010-2222-0001", "welfare_id": uuid.UUID("b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e"), "password": "demo1234"},
    {"id": uuid.UUID("d1000000-0000-4000-a000-000000000004"), "user_type": "youth", "name": "이영희",  "nickname": "이청년",   "email": "youth2@test.kr",  "phone": "010-2222-0002", "welfare_id": uuid.UUID("b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e"), "password": "demo1234"},
    {"id": uuid.UUID("d1000000-0000-4000-a000-000000000005"), "user_type": "youth", "name": "박지수",  "nickname": "박청년",   "email": "youth3@test.kr",  "phone": "010-2222-0003", "welfare_id": uuid.UUID("b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e"), "password": "demo1234"},
    {"id": uuid.UUID("d2000000-0000-4000-a000-000000000001"), "user_type": "elder", "name": "최옥순",  "nickname": "최어르신", "email": "elder3@test.kr",  "phone": "010-1111-0003", "welfare_id": uuid.UUID("c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f"), "password": "demo1234"},
]


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def seed():
    await create_tables()
    async with AsyncSessionLocal() as db:
        for w in SEED_WORKERS:
            existing = await db.execute(select(WelfareWorker).where(WelfareWorker.id == w["id"]))
            if existing.scalar_one_or_none():
                print(f"  SKIP (exists): WELFARE_WORKER id={w['id']} name={w['name']}")
                continue
            worker = WelfareWorker(
                id=w["id"],
                name=w["name"],
                email=w["email"],
                phone=w["phone"],
                password_hash=_hash_password(w["password"]),
                role=w["role"],
                region=w["region"],
            )
            db.add(worker)
            print(f"  CREATE: WELFARE_WORKER id={w['id']} name={w['name']}")

        for u in SEED_USERS:
            existing = await db.execute(select(User).where(User.id == u["id"]))
            if existing.scalar_one_or_none():
                print(f"  SKIP (exists): USER id={u['id']} nickname={u['nickname']}")
                continue
            user = User(
                id=u["id"],
                user_type=u["user_type"],
                name=u["name"],
                nickname=u["nickname"],
                email=u["email"],
                phone=u["phone"],
                password_hash=_hash_password(u["password"]),
                welfare_id=u["welfare_id"],
                is_anonymous=(u["user_type"] == "youth"),
            )
            db.add(user)
            print(f"  CREATE: USER id={u['id']} nickname={u['nickname']}")

        await db.commit()
        print(f"\nDone! {len(SEED_WORKERS)} workers, {len(SEED_USERS)} users seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
