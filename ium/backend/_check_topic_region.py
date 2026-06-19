import aiosqlite

async def check():
    conn = await aiosqlite.connect('local_ium.db')
    cur = await conn.execute("SELECT id, title, region, welfare_id FROM weekly_topics WHERE id = 'ad893edfeafa4649b2e3f6d27fd1ded3'")
    row = await cur.fetchone()
    print(f"Topic: {row}")
    await conn.close()

import asyncio
asyncio.run(check())
