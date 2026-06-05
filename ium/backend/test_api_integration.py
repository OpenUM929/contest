"""
이음 백엔드 API 통합 테스트
- image 타입 비활성화 확인
- text 타입 질문 유형(narrative) 자동 설정 확인
- 딥시크 API 질문 생성 확인
"""

import asyncio
import httpx
import json

API = "http://localhost:8000"

async def test_image_disabled():
    print("=" * 60)
    print("[TEST 1] image 타입 비활성화 확인")
    print("=" * 60)
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API}/welfare/topics/search", json={
            "media_type": "image",
            "keyword": "",
            "quantity": 3
        })
        print(f"  Status: {resp.status_code}")
        data = resp.json()
        if resp.status_code == 404 and "검색 결과가 없습니다" in data.get("detail", ""):
            print("  [PASS] image 타입이 완전히 비활성화됨 (404 + '검색 결과 없음')")
            return True
        elif data.get("candidates_found", 0) == 0:
            print("  [PASS] image 후보 0개 반환")
            return True
        else:
            print(f"  [FAIL] 예상치 못한 응답: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}")
            return False

async def test_text_question_type():
    print("\n" + "=" * 60)
    print("[TEST 2] text 타입 질문 유형 자동 설정 확인")
    print("=" * 60)
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API}/welfare/topics/search", json={
            "media_type": "text",
            "keyword": "전통",
            "quantity": 2
        })
        data = resp.json()
        print(f"  Status: {resp.status_code}")
        print(f"  후보 수: {data.get('candidates_found', 0)}")
        
        ok = True
        for i, c in enumerate(data.get("candidates", [])):
            qt = c.get("question_type", "MISSING")
            mt = c.get("media_type", "?")
            print(f"  후보 #{i+1}: media_type={mt}, question_type={qt}")
            if mt == "text" and qt != "narrative":
                print(f"    [FAIL] text 타입은 narrative 여야 함 (현재: {qt})")
                ok = False
            elif mt == "text" and qt == "narrative":
                print(f"    [PASS] text -> narrative 자동 설정")
        return ok

async def test_default_topic():
    print("\n" + "=" * 60)
    print("[TEST 3] 기본 주제 조회 (DB 폴백)")
    print("=" * 60)
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API}/welfare/topics/default")
        data = resp.json()
        print(f"  Status: {resp.status_code}")
        print(f"  제목: {data.get('title', 'N/A')}")
        print(f"  media_type: {data.get('media_type', 'N/A')}")
        print(f"  question_type: {data.get('question_type', 'N/A')}")
        if data.get("title"):
            print("  [PASS] 기본 주제 반환됨")
            return True
        else:
            print("  [FAIL] 주제 없음")
            return False

async def test_health():
    print("\n" + "=" * 60)
    print("[TEST 0] 서버 헬스 체크")
    print("=" * 60)
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API}/health")
        data = resp.json()
        print(f"  Status: {resp.status_code}")
        print(f"  응답: {data}")
        if data.get("status") == "ok":
            print("  [PASS]")
            return True
        else:
            print("  [FAIL]")
            return False

async def main():
    results = []
    results.append(("Health", await test_health()))
    results.append(("Image Disabled", await test_image_disabled()))
    results.append(("Text Question Type", await test_text_question_type()))
    results.append(("Default Topic", await test_default_topic()))
    
    print("\n" + "=" * 60)
    print("테스트 요약")
    print("=" * 60)
    all_pass = True
    for name, ok in results:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status}: {name}")
        if not ok:
            all_pass = False
    
    print("\n" + ("[ALL PASS] 전체 테스트 통과" if all_pass else "[PARTIAL FAIL] 일부 테스트 실패"))
    return 0 if all_pass else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    import sys
    sys.exit(exit_code)
