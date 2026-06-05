import sys, httpx, asyncio
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HEADERS = {"User-Agent": "IumProject/1.0 (welfare-app) python-httpx"}

URLS = [
    ("남대문시장", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Korea-Namdaemun_Market-01.jpg/800px-Korea-Namdaemun_Market-01.jpg"),
    ("골목풍경",   "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Seoul_back_alley.jpg/800px-Seoul_back_alley.jpg"),
    ("경복궁",     "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Gyeongbokgung.jpg/800px-Gyeongbokgung.jpg"),
    ("위키commons","https://commons.wikimedia.org/wiki/Main_Page"),
    ("구글",       "https://www.google.com"),
]

async def main():
    async with httpx.AsyncClient(timeout=15, headers=HEADERS, follow_redirects=True) as c:
        for title, url in URLS:
            try:
                r = await c.get(url)
                ct = r.headers.get("content-type", "?")[:40]
                print(f"{title}: HTTP {r.status_code}  size={len(r.content)}b  {ct}")
                if r.status_code != 200:
                    print(f"  body: {r.text[:200]}")
            except Exception as e:
                print(f"{title}: 예외 {e}")

asyncio.run(main())
