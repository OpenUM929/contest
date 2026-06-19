import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 키와 API가 반대로 매칭됨!
API1_URL = "https://api.kcisa.kr/API_CNV_048/request"
API2_URL = "https://api.kcisa.kr/openapi/API_CHA_084/request"
KEY_1 = "6479b947-04aa-4bc2-bae1-76e9c899ca9c"
KEY_2 = "3ab25e5f-c20e-4278-a6fa-8c0fdcd877a0"

# ===================== 2번 API (청주박물관) + 1번 키 =====================
print("=" * 70)
print("[테스트] 국립청주박물관_소장품 + 1번 키")
print("=" * 70)

params = {"serviceKey": KEY_1, "numOfRows": "10", "pageNo": "1"}
url = f"{API2_URL}?{urlencode(params)}"
resp = requests.get(url, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
print()

raw = resp.text
with open("cheongju_response.xml", "w", encoding="utf-8") as f:
    f.write(raw)

root = ET.fromstring(raw)
result_code = root.findtext('.//resultCode', default='N/A')
result_msg = root.findtext('.//resultMsg', default='N/A')
print(f"resultCode: {result_code}")
print(f"resultMsg: {result_msg}")
print()

items = root.findall('.//item')
print(f"데이터 항목 수: {len(items)}")
print()

image_urls = []
for idx, item in enumerate(items[:10]):
    title = item.findtext('TITLE', default='')
    alt_title = item.findtext('ALTERNATIVE_TITLE', default='')
    desc = item.findtext('DESCRIPTION', default='')
    img_url = item.findtext('IMAGE_OBJECT', default='')
    url_val = item.findtext('URL', default='')
    
    print(f"--- Item {idx+1} ---")
    print(f"  TITLE: {title}")
    print(f"  ALT_TITLE: {alt_title}")
    print(f"  DESCRIPTION: {desc[:60]}...")
    print(f"  IMAGE_OBJECT: {img_url}")
    print(f"  URL: {url_val}")
    print()
    
    if img_url and img_url.strip():
        image_urls.append({'title': title or alt_title, 'url': img_url.strip()})

# ===================== 이미지 다운로드 테스트 =====================
print("=" * 70)
print("[이미지 다운로드 테스트]")
print("=" * 70)
print()

for idx, info in enumerate(image_urls[:5]):
    test_url = info['url']
    print(f"[{idx+1}] Testing: {test_url}")
    try:
        img_resp = requests.get(test_url, timeout=30, allow_redirects=True)
        content_type = img_resp.headers.get('Content-Type', 'N/A')
        print(f"    Status: {img_resp.status_code}")
        print(f"    Content-Type: {content_type}")
        print(f"    Content-Length: {len(img_resp.content)} bytes")
        
        if 'image' in content_type.lower():
            print(f"    -> [SUCCESS] 이 URL은 이미지 데이터를 반환합니다!")
            safe_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_title:
                safe_title = f"img_{idx+1}"
            filename = f"cheongju_{safe_title[:20]}.jpg"
            with open(filename, 'wb') as f:
                f.write(img_resp.content)
            print(f"    -> 저장됨: {filename}")
        else:
            print(f"    -> [FAIL] 이미지가 아닙니다 ({content_type})")
        print()
    except Exception as e:
        print(f"    -> [ERROR] 호출 실패: {e}")
        print()

# ===================== 1번 API (중앙박물관) + 2번 키 =====================
print("\n" + "=" * 70)
print("[테스트] 국립중앙박물관 외_유물정보 + 2번 키")
print("=" * 70)

params1 = {"serviceKey": KEY_2, "numOfRows": "10", "pageNo": "1", "keyword": ""}
url1 = f"{API1_URL}?{urlencode(params1)}"
resp1 = requests.get(url1, timeout=30)
print(f"Status: {resp1.status_code}")
print(f"Content-Type: {resp1.headers.get('Content-Type', 'N/A')}")
print(f"Body: {resp1.text[:200]}")
print()

# JSON 응답일 수도 있으니 확인
if resp1.status_code == 200:
    try:
        data = resp1.json()
        print(f"JSON 응답: {data}")
    except:
        print("JSON 파싱 실패, XML 시도")
        try:
            root1 = ET.fromstring(resp1.text)
            rc = root1.findtext('.//resultCode', default='N/A')
            print(f"resultCode: {rc}")
        except Exception as e:
            print(f"XML 파싱도 실패: {e}")

print("\n" + "=" * 70)
print("[모든 테스트 완료]")
print("=" * 70)
