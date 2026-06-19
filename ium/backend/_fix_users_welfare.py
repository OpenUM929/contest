import aiosqlite
import asyncio

async def fix():
    conn = await aiosqlite.connect('local_ium.db')
    
    # Get welfare_worker id
    cur = await conn.execute("SELECT id FROM welfare_workers LIMIT 1")
    welfare = await cur.fetchone()
    if not welfare:
        print("No welfare worker found!")
        await conn.close()
        return
    
    welfare_id = welfare[0]
    print(f"WelfareWorker ID: {welfare_id}")
    
    # Update all users to have welfare_id
    cur = await conn.execute(
        "UPDATE users SET welfare_id = ? WHERE user_type IN ('elder', 'youth')",
        (welfare_id,)
    )
    await conn.commit()
    print(f"Updated {cur.rowcount} users")
    
    # Verify
    cur = await conn.execute("SELECT id, nickname, user_type, welfare_id FROM users WHERE user_type IN ('elder', 'youth')")
    users = await cur.fetchall()
    for u in users:
        print(f"  {u}")
    
    await conn.close()

asyncio.run(fix())
