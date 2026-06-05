"""
search_topic_candidates 전체 흐름 테스트
- KCISA 비활성화 상태
- 국가기록원 API만 호출
- 이미지 URL 없으면 TOPIC_POOL 샘플 폴백
"""

import asyncio
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from dotenv import load_dotenv
load_dotenv()

# DB 없이 public_data 함수만 임포트
from app.services.public_data import search_topic_candidates

async def test_image():
    print("=" * 60)
    print("이미지 후보 검색 테스트 (KCISA 미인증, 국가기록원은 이미지 아님)")
    print("= TOPIC_POOL 샘플(위키미디어)만 사용")
    print("=" * 60)
    
    candidates = await search_topic_candidates("image", keyword="전통", quantity=3)
    
    print(f"\n[결과] 총 후보: {len(candidates)}개")
    for i, c in enumerate(candidates):
        print(f"\n--- 후보 #{i+1} ---")
        print(f"  제목: {c['title'][:50]}")
        print(f"  media_url: {c.get('media_url', 'None')}")
        print(f"  source: {c.get('source', 'N/A')}")
        print(f"  media_type: {c.get('media_type', 'N/A')}")

async def test_text():
    print("\n" + "=" * 60)
    print("텍스트(이야기/기록물) 후보 검색 테스트")
    print("= 국가기록원 API 호출 + TOPIC_POOL 보충")
    print("=" * 60)
    
    candidates = await search_topic_candidates("text", keyword="전통", quantity=3)
    
    print(f"\n[결과] 총 후보: {len(candidates)}개")
    for i, c in enumerate(candidates):
        print(f"\n--- 후보 #{i+1} ---")
        print(f"  제목: {c['title'][:50]}")
        print(f"  설명: {c.get('description', 'None')[:100]}")
        print(f"  media_type: {c.get('media_type', 'N/A')}")
        print(f"  source: {c.get('source', 'N/A')}")

async def main():
    await test_image()
    await test_text()
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
