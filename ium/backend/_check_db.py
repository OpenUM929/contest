import aiosqlite
import asyncio

async def check():
    conn = await aiosqlite.connect('local_ium.db')
    cur = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = await cur.fetchall()
    print([t[0] for t in tables])
    await conn.close()

asyncio.run(check())
