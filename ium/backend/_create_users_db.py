import aiosqlite
import asyncio
import uuid

async def insert():
    conn = await aiosqlite.connect('local_ium.db')
    
    # Check existing users
    cur = await conn.execute("SELECT id, nickname, user_type FROM users")
    existing = await cur.fetchall()
    print(f"Existing users: {len(existing)}")
    
    # Get welfare_id
    cur = await conn.execute("SELECT id FROM welfare_workers LIMIT 1")
    welfare = await cur.fetchone()
    welfare_id = welfare[0] if welfare else None
    print(f"WelfareWorker ID: {welfare_id}")
    
    # Create users directly
    users_data = [
        (str(uuid.uuid4()), "elder", "김어르신", welfare_id, False),
        (str(uuid.uuid4()), "elder", "박어르신", welfare_id, False),
        (str(uuid.uuid4()), "elder", "최어르신", welfare_id, False),
        (str(uuid.uuid4()), "youth", "김청년", welfare_id, True),
        (str(uuid.uuid4()), "youth", "이청년", welfare_id, True),
        (str(uuid.uuid4()), "youth", "박청년", welfare_id, True),
    ]
    
    for uid, utype, nick, wid, anon in users_data:
        await conn.execute(
            "INSERT INTO users (id, user_type, nickname, welfare_id, is_anonymous, created_at, last_seen_at) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (uid, utype, nick, wid, anon)
        )
    
    await conn.commit()
    
    # Verify
    cur = await conn.execute("SELECT id, nickname, user_type FROM users WHERE user_type IN ('elder', 'youth')")
    users = await cur.fetchall()
    print(f"\nTotal users: {len(users)}")
    for u in users:
        print(f"  {u}")
    
    await conn.close()

asyncio.run(insert())
