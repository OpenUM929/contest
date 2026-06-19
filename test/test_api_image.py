import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import json
import sys

# PowerShell 한글 출력 문제 방지
sys.stdout.reconfigure(encoding='utf-8')

# API 설정
BASE_URL = "https://api.kcisa.kr/openapi/API_CCA_169/request"
SERVICE_KEY = "77f571ea-321d-464f-bbf0-f49597b5edb9"

# 1. API 호출 (XML 응답)
params = {
    "serviceKey": SERVICE_KEY,
    "numOfRows": "10",
    "pageNo": "1"
}

url = f"{BASE_URL}?{urlencode(params)}"

# 결과를 파일로 저장
with open("api_test_result.txt", "w", encoding="utf-8") as log:
    log.write("=" * 60 + "\n")
    log.write("[1] API 호출 URL\n")
    log.write("=" * 60 + "\n")
    log.write(url + "\n\n")

    response = requests.get(url, timeout=30)
    log.write("=" * 60 + "\n")
    log.write("[2] 응답 상태 코드\n")
    log.write("=" * 60 + "\n")
    log.write(f"Status Code: {response.status_code}\n")
    log.write(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}\n\n")

    # 응답 내용 저장
    raw_response = response.text
    log.write("=" * 60 + "\n")
    log.write("[3] 원본 응답 (앞 3000자)\n")
    log.write("=" * 60 + "\n")
    log.write(raw_response[:3000])
    if len(raw_response) > 3000:
        log.write("\n...\n")
    log.write("\n\n")

    # 4. XML 파싱
    try:
        root = ET.fromstring(raw_response)
        
        # 결과 코드 확인
        result_code = root.findtext('.//resultCode', default='N/A')
        result_msg = root.findtext('.//resultMsg', default='N/A')
        
        log.write("=" * 60 + "\n")
        log.write("[4] 결과 코드 및 메시지\n")
        log.write("=" * 60 + "\n")
        log.write(f"resultCode: {result_code}\n")
        log.write(f"resultMsg: {result_msg}\n\n")
        
        # item 목록 추출
        items = root.findall('.//item')
        log.write("=" * 60 + "\n")
        log.write(f"[5] 데이터 항목 수: {len(items)}\n")
        log.write("=" * 60 + "\n\n")
        
        # 각 항목의 URL 확인
        image_urls = []
        for idx, item in enumerate(items[:10]):  # 처음 10개 확인
            title = item.findtext('TITLE', default='N/A')
            url_val = item.findtext('URL', default='N/A')
            description = item.findtext('DESCRIPTION', default='N/A')
            
            log.write(f"--- Item {idx+1} ---\n")
            log.write(f"TITLE: {title}\n")
            log.write(f"URL: {url_val}\n")
            log.write(f"DESCRIPTION: {description[:200]}...\n\n")
            
            if url_val and url_val != 'N/A':
                image_urls.append({
                    'title': title,
                    'url': url_val
                })
        
        # 6. URL에서 이미지 호출 테스트
        log.write("=" * 60 + "\n")
        log.write("[6] 이미지 호출 가능 여부 테스트\n")
        log.write("=" * 60 + "\n\n")
        
        for info in image_urls[:5]:
            test_url = info['url']
            log.write(f"Testing: {test_url}\n")
            try:
                img_resp = requests.get(test_url, timeout=30, allow_redirects=True)
                content_type = img_resp.headers.get('Content-Type', 'N/A')
                log.write(f"  Status: {img_resp.status_code}\n")
                log.write(f"  Content-Type: {content_type}\n")
                log.write(f"  Content-Length: {len(img_resp.content)} bytes\n")
                
                if 'image' in content_type.lower():
                    log.write(f"  -> [SUCCESS] 이 URL은 이미지 데이터를 반환합니다!\n")
                    # 이미지 저장
                    safe_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    if not safe_title:
                        safe_title = f"image_{idx+1}"
                    filename = f"test_image_{safe_title[:20]}.jpg"
                    with open(filename, 'wb') as f:
                        f.write(img_resp.content)
                    log.write(f"  -> 저장됨: {filename}\n")
                else:
                    log.write(f"  -> [FAIL] 이 URL은 이미지가 아닙니다 (HTML/기타)\n")
                log.write("\n")
            except Exception as e:
                log.write(f"  -> [ERROR] 호출 실패: {e}\n\n")

    except Exception as e:
        log.write(f"XML 파싱 오류: {e}\n")
        log.write("응답이 XML 형식이 아닐 수 있습니다.\n\n")

    log.write("=" * 60 + "\n")
    log.write("[7] 완료\n")
    log.write("=" * 60 + "\n")

print("테스트 완료. 결과는 api_test_result.txt 에 저장되었습니다.")
