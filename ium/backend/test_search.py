import asyncio
import os

os.environ["ENVIRONMENT"] = "local"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./local_ium.db"
os.environ["SKIP_EMOTION"] = "true"
os.environ["MEDIA_CACHE_DIR"] = "./local_media_cache"

from app.services.public_data import search_topic_candidates

async def test():
    try:
        result = await search_topic_candidates("image", "", 3)
        print(f"Success: {len(result)} candidates")
        for r in result:
            print(f"  - {r['title']} ({r['media_type']})")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
