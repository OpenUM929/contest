import aiosqlite
import asyncio

async def check():
    conn = await aiosqlite.connect('local_ium.db')
    
    # 테이블 컬럼 확인
    cur = await conn.execute("PRAGMA table_info(survey_templates)")
    cols = await cur.fetchall()
    print("survey_templates columns:")
    for c in cols:
        print(f"  {c}")
    
    # 최근 데이터 확인
    cur = await conn.execute("SELECT * FROM survey_templates ORDER BY created_at DESC LIMIT 2")
    surveys = await cur.fetchall()
    print("\nSurveyTemplates data:")
    for s in surveys:
        print(f"  {s}")
    
    await conn.close()

asyncio.run(check())
