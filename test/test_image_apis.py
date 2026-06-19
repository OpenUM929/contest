import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import sys

# PowerShell 한글 출력 문제 방지
sys.stdout.reconfigure(encoding='utf-8')

# ========== 1번 API: 국립중앙박물관 외_유물정보(주요유물) ==========
API1_URL = "https://api.kcisa.kr/API_CNV_048/request"
API1_KEY = "6479b947-04aa-4bc2-bae1-76e9c899ca9c"
API1_NAME = "국립중앙박물관 외_유물정보(주요유물)"

# ========== 2번 API: 국립청주박물관_소장품 ==========
API2_URL = "https://api.kcisa.kr/openapi/API_CHA_084/request"
API2_KEY = "3ab25e5f-c20e-4278-a6fa-8c0fdcd877a0"
API2_NAME = "국립청주박물관_소장품"


def test_api(api_name, base_url, service_key, image_field_name, extra_params=None):
    print("=" * 70)
    print(f"[테스트 시작] {api_name}")
    print("=" * 70)
    
    params = {
        "serviceKey": service_key,
        "numOfRows": "10",
        "pageNo": "1"
    }
    if extra_params:
        params.update(extra_params)
    
    url = f"{base_url}?{urlencode(params)}"
    print(f"[요청 URL] {url}")
    print()
    
    try:
        response = requests.get(url, timeout=30)
        print(f"[응답 상태] {response.status_code}")
        print(f"[Content-Type] {response.headers.get('Content-Type', 'N/A')}")
        print()
    except Exception as e:
        print(f"[API 호출 실패] {e}")
        return []
    
    raw = response.text
    # 결과를 파일로도 저장
    safe_name = api_name.replace(" ", "_").replace("/", "_")
    with open(f"{safe_name}_response.xml", "w", encoding="utf-8") as f:
        f.write(raw)
    
    # XML 파싱
    try:
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"[XML 파싱 실패] {e}")
        print("[원본 응답 앞 500자]", raw[:500])
        return []
    
    result_code = root.findtext('.//resultCode', default='N/A')
    result_msg = root.findtext('.//resultMsg', default='N/A')
    print(f"[resultCode] {result_code}")
    print(f"[resultMsg] {result_msg}")
    print()
    
    if result_code != '0000':
        print("[오류] API 호출 결과가 정상이 아닙니다.")
        return []
    
    items = root.findall('.//item')
    print(f"[데이터 항목 수] {len(items)}")
    print()
    
    image_urls = []
    for idx, item in enumerate(items[:5]):  # 처음 5개만 확인
        title = item.findtext('title', default='') or item.findtext('TITLE', default='')
        desc = item.findtext('description', default='') or item.findtext('DESCRIPTION', default='')
        img_url = item.findtext(image_field_name, default='')
        
        print(f"--- Item {idx+1} ---")
        print(f"  제목: {title[:50]}")
        print(f"  {image_field_name}: {img_url}")
        print()
        
        if img_url and img_url.strip():
            image_urls.append({
                'title': title,
                'url': img_url.strip()
            })
    
    return image_urls


def test_image_download(image_urls, api_name):
    if not image_urls:
        print("[이미지 URL 없음] 테스트할 이미지가 없습니다.")
        return
    
    print("=" * 70)
    print(f"[이미지 다운로드 테스트] {api_name}")
    print("=" * 70)
    print()
    
    for idx, info in enumerate(image_urls[:3]):
        test_url = info['url']
        print(f"Testing: {test_url}")
        try:
            img_resp = requests.get(test_url, timeout=30, allow_redirects=True)
            content_type = img_resp.headers.get('Content-Type', 'N/A')
            print(f"  Status: {img_resp.status_code}")
            print(f"  Content-Type: {content_type}")
            print(f"  Content-Length: {len(img_resp.content)} bytes")
            
            if 'image' in content_type.lower():
                print(f"  -> [SUCCESS] 이미지 데이터 확인!")
                safe_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                if not safe_title:
                    safe_title = f"img_{idx+1}"
                filename = f"{api_name.replace(' ', '_').replace('/', '_')}_img_{safe_title[:20]}.jpg"
                with open(filename, 'wb') as f:
                    f.write(img_resp.content)
                print(f"  -> 저장됨: {filename}")
            else:
                print(f"  -> [FAIL] 이미지가 아닙니다 ({content_type})")
            print()
        except Exception as e:
            print(f"  -> [ERROR] 호출 실패: {e}")
            print()


# ====================== 실행 ======================

# 1번 API 테스트
urls1 = test_api(API1_NAME, API1_URL, API1_KEY, "imageObject", extra_params={"keyword": ""})
test_image_download(urls1, API1_NAME)

print("\n" + "=" * 70 + "\n")

# 2번 API 테스트
urls2 = test_api(API2_NAME, API2_URL, API2_KEY, "IMAGE_OBJECT")
test_image_download(urls2, API2_NAME)

print("\n" + "=" * 70)
print("[모든 테스트 완료]")
print("=" * 70)
