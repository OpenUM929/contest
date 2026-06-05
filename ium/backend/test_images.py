"""
이미지 수집 종합 테스트
1. 공공 API 키 유효성 (민속박물관, 국가기록원)
2. API 응답에서 이미지 URL 추출 가능 여부
3. TOPIC_POOL 폴백 이미지 URL 접근 가능 여부
4. 실제 이미지 다운로드 및 저장 테스트
"""

import os
import sys
import asyncio
import xml.etree.ElementTree as ET

# Windows 콘솔 UTF-8 강제 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import httpx

# Wikimedia 등 외부 이미지 서버가 요구하는 User-Agent
HEADERS = {
    "User-Agent": "IumProject/1.0 (welfare-app; contact@example.com) python-httpx"
}

# .env 로드 (python-dotenv 없어도 직접 파싱)
def load_env(path=".env"):
    env = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env

env = load_env(os.path.join(os.path.dirname(__file__), ".env"))
API_KEY = env.get("PUBLIC_DATA_API_KEY", os.getenv("PUBLIC_DATA_API_KEY", ""))

# TOPIC_POOL 폴백 이미지 URL 목록
FALLBACK_IMAGES = [
    {
        "title": "1960년대 서울 남대문 시장",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Korea-Namdaemun_Market-01.jpg/800px-Korea-Namdaemun_Market-01.jpg",
    },
    {
        "title": "1980년대 동네 골목 풍경",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Seoul_back_alley.jpg/800px-Seoul_back_alley.jpg",
    },
    {
        "title": "경복궁",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Gyeongbokgung.jpg/800px-Gyeongbokgung.jpg",
    },
]

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"
WARN = "[WARN]"

def sep(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


async def test_folk_museum(client: httpx.AsyncClient) -> list[str]:
    """민속박물관 API 테스트 -> 이미지 URL 목록 반환"""
    sep("1. 민속박물관 API (api.kcisa.kr)")
    url = "https://api.kcisa.kr/openapi/service/rest/meta/NFMphot"
    params = {"serviceKey": API_KEY, "numOfRows": 5, "pageNo": 1, "keyword": "전통"}

    try:
        resp = await client.get(url, params=params)
        print(f"{INFO} HTTP {resp.status_code}")

        if resp.status_code != 200:
            print(f"{FAIL} 응답 오류: {resp.text[:300]}")
            return []

        root = ET.fromstring(resp.text)
        code = root.findtext(".//resultCode", "")
        msg  = root.findtext(".//resultMsg", "")
        print(f"{INFO} resultCode={code}  resultMsg={msg}")

        if code != "00":
            print(f"{FAIL} API 거부 (코드 불일치)")
            return []

        items = root.findall(".//item")
        print(f"{INFO} item 수: {len(items)}")

        urls = []
        for i, item in enumerate(items[:3]):
            identifier = item.findtext("identifier", "")
            title      = item.findtext("title", "(제목없음)")[:40]
            print(f"\n  item #{i+1}: {title}")
            print(f"    identifier: {identifier[:80] if identifier else '(없음)'}")
            if identifier and identifier.startswith("http"):
                urls.append(identifier)
                print(f"    {PASS} 이미지 URL 발견")
            else:
                print(f"    {WARN} 이미지 URL 없음")

        return urls

    except Exception as e:
        print(f"{FAIL} 예외: {type(e).__name__}: {e}")
        return []


async def test_archives(client: httpx.AsyncClient) -> list[str]:
    """국가기록원 API 테스트 -> 이미지 URL 목록 반환"""
    sep("2. 국가기록원 API (apis.data.go.kr)")
    url = "https://apis.data.go.kr/1741050/openapi"
    params = {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 5, "searchKeyword": "시장"}

    try:
        resp = await client.get(url, params=params)
        print(f"{INFO} HTTP {resp.status_code}")

        if resp.status_code != 200:
            print(f"{FAIL} 응답 오류: {resp.text[:300]}")
            return []

        ct = resp.headers.get("content-type", "")
        print(f"{INFO} Content-Type: {ct}")

        if "json" in ct:
            data = resp.json()
            print(f"{INFO} JSON 응답 키: {list(data.keys())[:5]}")
            return []

        root = ET.fromstring(resp.text)
        code = root.findtext(".//resultCode", "")
        msg  = root.findtext(".//resultMsg", "")
        print(f"{INFO} resultCode={code}  resultMsg={msg}")

        items = root.findall(".//item")
        print(f"{INFO} item 수: {len(items)}")

        urls = []
        for i, item in enumerate(items[:3]):
            title  = (item.findtext("recordTitle", "") or item.findtext("title", "(제목없음)"))[:40]
            thumb  = item.findtext("thumbnailUrl", "")
            imgurl = item.findtext("imageUrl", "")
            print(f"\n  item #{i+1}: {title}")
            for label, val in [("thumbnailUrl", thumb), ("imageUrl", imgurl)]:
                if val:
                    print(f"    {label}: {val[:80]}")
                    if val.startswith("http"):
                        urls.append(val)
                        print(f"    {PASS} 이미지 URL 발견")
                else:
                    print(f"    {label}: (없음)")

        return urls

    except Exception as e:
        print(f"{FAIL} 예외: {type(e).__name__}: {e}")
        return []


async def test_url_access(client: httpx.AsyncClient, url: str, label: str) -> bool:
    """HEAD 요청으로 URL 접근 가능 여부 확인"""
    try:
        resp = await client.head(url, follow_redirects=True)
        ok = resp.status_code == 200
        status = PASS if ok else FAIL
        ctype = resp.headers.get("content-type", "")
        size  = resp.headers.get("content-length", "?")
        print(f"  {status} {label}")
        print(f"       HTTP {resp.status_code}  {ctype}  size={size}bytes")
        return ok
    except Exception as e:
        print(f"  {FAIL} {label}")
        print(f"       예외: {type(e).__name__}: {e}")
        return False


async def test_download(client: httpx.AsyncClient, url: str, save_path: str) -> bool:
    """실제 이미지 다운로드 테스트"""
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            print(f"  {FAIL} 다운로드 실패: HTTP {resp.status_code}")
            return False
        with open(save_path, "wb") as f:
            f.write(resp.content)
        size_kb = len(resp.content) / 1024
        print(f"  {PASS} 다운로드 성공: {size_kb:.1f} KB -> {save_path}")
        return True
    except Exception as e:
        print(f"  {FAIL} 다운로드 예외: {type(e).__name__}: {e}")
        return False


async def main():
    print("=" * 60)
    print("  이미지 수집 종합 테스트")
    print("=" * 60)
    print(f"{INFO} API_KEY 길이: {len(API_KEY)}")
    if API_KEY:
        print(f"{INFO} API_KEY 앞 10자: {API_KEY[:10]}...")
    else:
        print(f"{WARN} API_KEY 미설정")

    results = {
        "folk_museum_api": False,
        "archives_api":    False,
        "fallback_urls":   0,
        "download_test":   False,
    }

    # 공공 API는 기본 헤더, 위키미디어는 User-Agent 필요
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:

        # 1/2. 공공 API 테스트
        folk_urls    = await test_folk_museum(client)
        archive_urls = await test_archives(client)

        results["folk_museum_api"] = len(folk_urls) > 0
        results["archives_api"]    = len(archive_urls) > 0

        all_api_urls = folk_urls + archive_urls

        # 3. API URL 접근 테스트
        if all_api_urls:
            sep("3. 공공 API 이미지 URL 접근 테스트")
            for u in all_api_urls[:3]:
                await test_url_access(client, u, u[:60])

        # 4. TOPIC_POOL 폴백 이미지 URL 접근 테스트
        sep("4. TOPIC_POOL 폴백 이미지 URL 접근 테스트 (위키미디어)")
        accessible = 0
        first_ok_url = None
        first_ok_title = ""
        for item in FALLBACK_IMAGES:
            ok = await test_url_access(client, item["url"], item["title"])
            if ok:
                accessible += 1
                if first_ok_url is None:
                    first_ok_url   = item["url"]
                    first_ok_title = item["title"]
        results["fallback_urls"] = accessible
        print(f"\n{INFO} 접근 가능: {accessible}/{len(FALLBACK_IMAGES)}")

        # 5. 실제 다운로드 테스트
        sep("5. 실제 다운로드 테스트")
        download_url   = None
        download_label = ""

        if all_api_urls:
            download_url   = all_api_urls[0]
            download_label = "공공 API 이미지"
        elif first_ok_url:
            download_url   = first_ok_url
            download_label = first_ok_title

        if download_url:
            os.makedirs("test_download_output", exist_ok=True)
            save_path = os.path.join("test_download_output", "test_image.jpg")
            print(f"{INFO} 다운로드 대상: {download_label}")
            print(f"       {download_url[:70]}")
            results["download_test"] = await test_download(client, download_url, save_path)
        else:
            print(f"{WARN} 다운로드 가능한 URL 없음")

    # 최종 요약
    sep("최종 결과 요약")
    checks = [
        ("민속박물관 API 이미지 URL 추출",  results["folk_museum_api"]),
        ("국가기록원 API 이미지 URL 추출",  results["archives_api"]),
        (f"폴백 이미지 URL 접근 ({results['fallback_urls']}/{len(FALLBACK_IMAGES)}개)", results["fallback_urls"] > 0),
        ("실제 이미지 다운로드",            results["download_test"]),
    ]
    all_ok = True
    for label, ok in checks:
        icon = PASS if ok else FAIL
        print(f"  {icon} {label}")
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print("  전체 통과 - 이미지 파이프라인 정상")
    elif results["fallback_urls"] > 0 or results["download_test"]:
        print("  공공 API 실패, 폴백 이미지는 정상 - 우선 폴백으로 서비스 가능")
    else:
        print("  이미지를 전혀 가져올 수 없음 - 조치 필요")

    print("=" * 60)
    return 0 if (results["fallback_urls"] > 0 or results["folk_museum_api"] or results["archives_api"]) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
