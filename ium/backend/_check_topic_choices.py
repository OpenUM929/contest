import aiosqlite
import asyncio

async def check():
    conn = await aiosqlite.connect('local_ium.db')
    cur = await conn.execute("SELECT id, title, question_type, choices FROM weekly_topics WHERE id = 'ad893edfeafa4649b2e3f6d27fd1ded3'")
    row = await cur.fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"Title: {row[1]}")
        print(f"Question Type: {row[2]}")
        print(f"Choices: {row[3]}")
    else:
        print("Topic not found")
    await conn.close()

asyncio.run(check())
