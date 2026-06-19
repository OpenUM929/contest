import aiosqlite
import asyncio

async def check():
    conn = await aiosqlite.connect('local_ium.db')
    cur = await conn.execute("SELECT id, title, media_type, question_type, welfare_id, active_week FROM weekly_topics ORDER BY created_at DESC LIMIT 3")
    rows = await cur.fetchall()
    print("WeeklyTopic count this week:", len(rows))
    for r in rows:
        print(r)
    await conn.close()

asyncio.run(check())
