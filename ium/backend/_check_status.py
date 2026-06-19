import aiosqlite
import asyncio

async def check():
    conn = await aiosqlite.connect('local_ium.db')
    
    # Users 확인
    cur = await conn.execute("SELECT id, nickname, user_type, last_seen_at FROM users LIMIT 10")
    users = await cur.fetchall()
    print("Users:")
    for u in users:
        print(f"  {u}")
    
    # WeeklyTopic 확인
    cur = await conn.execute("SELECT id, title, question_type, choices FROM weekly_topics ORDER BY created_at DESC LIMIT 2")
    topics = await cur.fetchall()
    print("\nWeeklyTopics:")
    for t in topics:
        print(f"  ID: {t[0]}, Title: {t[1]}, Type: {t[2]}")
    
    # SurveyResponse 확인
    cur = await conn.execute("SELECT COUNT(*) FROM survey_responses")
    count = await cur.fetchone()
    print(f"\nSurveyResponses count: {count[0]}")
    
    await conn.close()

asyncio.run(check())
