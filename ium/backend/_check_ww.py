import aiosqlite
import asyncio

async def check():
    conn = await aiosqlite.connect('local_ium.db')
    cur = await conn.execute("SELECT id, name, region, email FROM welfare_workers LIMIT 5")
    rows = await cur.fetchall()
    print("WelfareWorker count:", len(rows))
    for r in rows:
        print(r)
    await conn.close()

asyncio.run(check())
