"""
공공데이터포털 API 테스트 - 국가기록원
"""

import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import httpx

load_dotenv()
PUB_KEY = os.getenv("PUBLIC_DATA_API_KEY", "")
print(f"[INFO] PUBLIC_DATA_API_KEY (국가기록원): {PUB_KEY}")
print()

# ────────────────────────────────
# 국가기록원 API (공공데이터포털)
# ────────────────────────────────
print("=" * 60)
print("국가기록원 API (공공데이터포털)")
print("=" * 60)

url = "https://apis.data.go.kr/1741050/openapi"
params = {
    "serviceKey": PUB_KEY,
    "pageNo": 1,
    "numOfRows": 5,
    "searchKeyword": "시장"
}

try:
    resp = httpx.get(url, params=params, timeout=30)
    print(f"[HTTP] Status: {resp.status_code}")
    print(f"[HTTP] URL: {resp.url}")
    
    if resp.status_code == 200:
        print(f"[RESPONSE] {resp.text[:2000]}")
    else:
        print(f"[ERROR] Status {resp.status_code}")
        print(f"[BODY] {resp.text[:1000]}")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)
