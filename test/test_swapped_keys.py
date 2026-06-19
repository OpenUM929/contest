import requests
from urllib.parse import urlencode

# 키 교차 테스트
key1 = '6479b947-04aa-4bc2-bae1-76e9c899ca9c'
key2 = '3ab25e5f-c20e-4278-a6fa-8c0fdcd877a0'

# 1번 API (국립중앙박물관 유물정보)에 2번 키
params1 = {"serviceKey": key2, "numOfRows": "10", "pageNo": "1", "keyword": ""}
url1 = f"https://api.kcisa.kr/API_CNV_048/request?{urlencode(params1)}"
resp1 = requests.get(url1, timeout=30)
print(f"[1번 API + 2번 키] Status: {resp1.status_code}")
print(f"  Body: {resp1.text[:100]}")
print()

# 2번 API (국립청주박물관 소장품)에 1번 키
params2 = {"serviceKey": key1, "numOfRows": "10", "pageNo": "1"}
url2 = f"https://api.kcisa.kr/openapi/API_CHA_084/request?{urlencode(params2)}"
resp2 = requests.get(url2, timeout=30)
print(f"[2번 API + 1번 키] Status: {resp2.status_code}")
print(f"  Body: {resp2.text[:100]}")
print()

# 추가: 원래 키로도 한 번 더 확인
print("="*50)
print("[원래 키 재확인]")
print("="*50)
resp3 = requests.get(f"https://api.kcisa.kr/API_CNV_048/request?{urlencode({'serviceKey': key1, 'numOfRows': '10', 'pageNo': '1', 'keyword': ''})}", timeout=30)
print(f"[1번 API + 1번 키] Status: {resp3.status_code}")

resp4 = requests.get(f"https://api.kcisa.kr/openapi/API_CHA_084/request?{urlencode({'serviceKey': key2, 'numOfRows': '10', 'pageNo': '1'})}", timeout=30)
print(f"[2번 API + 2번 키] Status: {resp4.status_code}")
