import aiosqlite
import asyncio

async def check():
    conn = await aiosqlite.connect('local_ium.db')
    
    # 최근 주제 확인
    cur = await conn.execute("SELECT id, title, question_type, welfare_id FROM weekly_topics ORDER BY created_at DESC LIMIT 2")
    topics = await cur.fetchall()
    print("Recent topics:")
    for t in topics:
        print(f"  {t}")
    
    # SurveyTemplate 확인
    cur = await conn.execute("SELECT id, topic_id, question_type, choices FROM survey_templates ORDER BY created_at DESC LIMIT 2")
    surveys = await cur.fetchall()
    print("\nSurveyTemplates:")
    for s in surveys:
        print(f"  {s}")
    
    await conn.close()

asyncio.run(check())
