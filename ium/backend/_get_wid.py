import asyncio, os, sys
os.environ["ENVIRONMENT"] = "local"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./local_ium.db"
os.environ["SKIP_EMOTION"] = "true"

from app.database import AsyncSessionLocal
from app.models.models import WelfareWorker
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(WelfareWorker))
        for w in r.scalars().all():
            print(str(w.id))

asyncio.run(main())
