"""
공공데이터 수집 및 주제 선정 서비스
- 민속박물관 API 연동 (XML)
- 미디어 캐싱 (로컬 파일시스템)
- AI 질문 자동 생성 (OpenCode 서버 기반 JSON 스키마 강제)
- 지역 기반 주제 조회
"""

import random
import os
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Any
from pathlib import Path

import httpx
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.models import WeeklyTopic
from app.services.question_parser import QuestionSet, QuestionItem, ChoiceOption, DEFAULT_FALLBACK

# OpenCode Zen API 설정
OPENCODE_BASE_URL = getattr(settings, "opencode_base_url", "https://opencode.ai/zen/v1")
OPENCODE_MODEL = getattr(settings, "opencode_model", "big-pickle")


async def _call_opencode_chat(prompt: str) -> str | None:
    """OpenCode Zen API에 직접 OpenAI compatible 호출을 수행합니다."""
    if not settings.opencode_api_key:
        print("[PublicData] OPENCODE_API_KEY 미설정")
        return None

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{OPENCODE_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.opencode_api_key}"},
                json={
                    "model": OPENCODE_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"[PublicData] OpenCode API 오류: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"[PublicData] OpenCode API 호출 실패: {e}")
    return None


async def _generate_with_opencode(prompt: str) -> QuestionSet | None:
    """OpenCode Zen API로 QuestionSet을 생성합니다."""
    raw_text = await _call_opencode_chat(prompt)
    if not raw_text:
        return None

    # JSON 블록 추출 (```json ... ```)
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json")[-1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[-1].split("```")[0].strip()

    try:
        data = json.loads(text)
        return QuestionSet.model_validate(data)
    except Exception as e:
        print(f"[PublicData] QuestionSet 파싱 실패: {e}")
        print(f"[PublicData] 원본 응답: {raw_text[:500]}")
        return None


PROMPT_DIR = Path(__file__).parent.parent / "prompts"

# 폴백용 샘플 풀 (API 실패 시 사용) - 위키미디어 퍼블릭 도메인 이미지
TOPIC_POOL = [
    {
        "title": "1960년대 서울 남대문 시장",
        "description": "분주한 장터의 활기 속에 사람들의 일상이 담겨 있습니다.",
        "media_type": "image",
        "media_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Korea-Namdaemun_Market-01.jpg/800px-Korea-Namdaemun_Market-01.jpg",
        "source": "국가기록원",
        "source_url": "https://www.archives.go.kr",
        "ai_question": "이런 시장에 가보신 적 있으신가요? 그때 어떤 것을 사셨나요?",
        "text_content": None,
        "question_type": "mixed",
        "choices": {
            "schema_version": "1.0",
            "question_type": "mixed",
            "questions": [
                {
                    "id": "q1",
                    "type": "choice",
                    "text": "남대문 시장에 가본 적이 있으신가요?",
                    "target_age": "elderly",
                    "allow_multiple": False,
                    "options": [
                        {"id": "opt_1", "label": "네, 자주 갔어요", "value": "yes"},
                        {"id": "opt_2", "label": "가끔 갔었어요", "value": "sometimes"},
                        {"id": "opt_3", "label": "아니오, 들어만 봤어요", "value": "no"},
                    ],
                },
                {
                    "id": "q2",
                    "type": "narrative",
                    "text": "시장에서 가장 기억에 남는 순간을 이야기해 주세요.",
                    "target_age": "elderly",
                    "placeholder": "그날의 이야기를 들려주세요...",
                    "guidelines": ["누구와 함께", "무엇을 했는지"],
                },
            ],
        },
    },
    {
        "title": "1970년대 경기민요 - 창부타령",
        "description": "경기 지방을 대표하는 민요로, 흥겨운 리듬이 특징입니다.",
        "media_type": "audio",
        "media_url": None,
        "source": "국립국악원",
        "source_url": "https://www.gugak.go.kr",
        "ai_question": "이 노래를 들어보신 적 있으신가요? 어떤 장면이 떠오르세요?",
        "text_content": None,
        "question_type": "choice",
        "choices": {
            "schema_version": "1.0",
            "question_type": "choice",
            "questions": [
                {
                    "id": "q1",
                    "type": "choice",
                    "text": "이 노래를 들어보신 적 있으신가요?",
                    "target_age": "elderly",
                    "allow_multiple": False,
                    "has_other": True,
                    "options": [
                        {"id": "opt_1", "label": "농사일 할 때", "value": "A", "icon_hint": "🌾"},
                        {"id": "opt_2", "label": "명절 잔치 때", "value": "B", "icon_hint": "🎉"},
                        {"id": "opt_3", "label": "어릴 때 동네에서", "value": "C", "icon_hint": "🏘️"},
                        {"id": "opt_4", "label": "처음 들어요", "value": "D", "icon_hint": "🎧"},
                        {"id": "opt_other", "label": "기타 (직접 말씀해 주세요)", "value": "OTHER", "is_other": True},
                    ],
                }
            ],
        },
    },
    {
        "title": "삼신할머니 설화 - 새 생명을 점지하는 신",
        "description": "아이의 출생을 관장한다고 믿어진 민속 신앙 속 이야기입니다.",
        "media_type": "text",
        "media_url": None,
        "source": "국립민속박물관",
        "source_url": "https://www.nfm.go.kr",
        "ai_question": "어릴 때 이런 이야기를 들어보신 적 있으신가요?",
        "text_content": "옛날 옛적에 아이를 낳는 것을 돕는 삼신할머니가 계셨습니다...",
        "question_type": "narrative",
        "choices": {
            "schema_version": "1.0",
            "question_type": "narrative",
            "questions": [
                {
                    "id": "q1",
                    "type": "narrative",
                    "text": "어릴 때 이런 이야기를 들어보신 적 있으신가요?",
                    "target_age": "elderly",
                    "placeholder": "그때 어머니나 할머니가 들려주셨던 이야기를 떠올려 보세요...",
                    "guidelines": ["누가 들려주셨는지", "어떤 내용이었는지", "그때 기분은 어땠는지"],
                    "suggested_duration_seconds": 45,
                }
            ],
        },
    },
    {
        "title": "1980년대 동네 골목 풍경",
        "description": "아이들이 뛰어놀던 골목, 평상 위의 어른들, 연탄 가게의 기억.",
        "media_type": "image",
        "media_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Seoul_back_alley.jpg/800px-Seoul_back_alley.jpg",
        "source": "국가기록원",
        "source_url": "https://www.archives.go.kr",
        "ai_question": "어릴 때 살던 동네 골목은 어떤 모습이었나요?",
        "text_content": None,
        "question_type": "mixed",
        "choices": {
            "schema_version": "1.0",
            "question_type": "mixed",
            "questions": [
                {
                    "id": "q1",
                    "type": "choice",
                    "text": "어릴 때 동네 골목이 기억나시나요?",
                    "target_age": "elderly",
                    "allow_multiple": False,
                    "has_other": True,
                    "options": [
                        {"id": "opt_1", "label": "네, 뛰어놀던 골목", "value": "A", "icon_hint": "🏃"},
                        {"id": "opt_2", "label": "아파트에서 자랐어요", "value": "B", "icon_hint": "🏢"},
                        {"id": "opt_3", "label": "시골 마을이었어요", "value": "C", "icon_hint": "🌳"},
                        {"id": "opt_other", "label": "기타 (직접 말씀해 주세요)", "value": "OTHER", "is_other": True},
                    ],
                },
                {
                    "id": "q2",
                    "type": "narrative",
                    "text": "그곳에서 가장 기억에 남는 순간을 이야기해 주세요.",
                    "target_age": "elderly",
                    "placeholder": "그날의 이야기를 들려주세요...",
                    "guidelines": ["누구와 함께", "무엇을 했는지", "그때 기분은 어땠는지"],
                },
            ],
        },
    },
    {
        "title": "추석 명절 상차림",
        "description": "감사한 마음을 담아 정성껏 차리는 명절 음식의 추억.",
        "media_type": "text",
        "media_url": None,
        "source": "이음",
        "source_url": "",
        "ai_question": "추석 때 상차림에 어떤 음식이 올랐는지 기억나세요?",
        "text_content": None,
        "question_type": "narrative",
        "choices": None,
    },
    {
        "title": "어머니의 손맛",
        "description": "정성 가득한 집밥의 따뜻한 기억.",
        "media_type": "text",
        "media_url": None,
        "source": "이음",
        "source_url": "",
        "ai_question": "어머니가 해주신 가장 기억에 남는 음식은 무엇인가요?",
        "text_content": None,
        "question_type": "narrative",
        "choices": None,
    },
    {
        "title": "어릴 적 놀이터",
        "description": "뛰어놀던 골목과 친구들의 웃음소리.",
        "media_type": "text",
        "media_url": None,
        "source": "이음",
        "source_url": "",
        "ai_question": "어릴 때 자주 가던 놀이터는 어디였나요?",
        "text_content": None,
        "question_type": "narrative",
        "choices": None,
    },
    {
        "title": "경복궁 - 조선의 법궁",
        "description": "600년 역사를 품은 궁궐. 계절마다 다른 얼굴을 보여줍니다.",
        "media_type": "image",
        "media_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Gyeongbokgung.jpg/800px-Gyeongbokgung.jpg",
        "source": "국가유산포털",
        "source_url": "https://www.heritage.go.kr",
        "ai_question": "경복궁에 가보신 적 있으신가요? 그때 어떤 느낌이었나요?",
        "text_content": None,
        "question_type": "choice",
        "choices": {
            "schema_version": "1.0",
            "question_type": "choice",
            "questions": [
                {
                    "id": "q1",
                    "type": "choice",
                    "text": "경복궁에 가보신 적 있으신가요?",
                    "target_age": "elderly",
                    "allow_multiple": False,
                    "has_other": True,
                    "options": [
                        {"id": "opt_1", "label": "어릴 때 학교견학", "value": "A", "icon_hint": "🎒"},
                        {"id": "opt_2", "label": "어른 되어 관광", "value": "B", "icon_hint": "📸"},
                        {"id": "opt_3", "label": "사진으로만 봤어요", "value": "C", "icon_hint": "🖼️"},
                        {"id": "opt_4", "label": "가보고 싶어요", "value": "D", "icon_hint": "✨"},
                        {"id": "opt_other", "label": "기타 (직접 말씀해 주세요)", "value": "OTHER", "is_other": True},
                    ],
                }
            ],
        },
    },
]


async def fetch_folk_museum(keyword: str = "") -> list[dict] | None:
    """
    KCISA 문화공공데이터광장 - 민속박물관 민속아카이브 사진자료 API
    
    [공식 정보]
    - 엔드포인트: https://api.kcisa.kr/openapi/API_CIA_092/request
    - 메서드: GET
    - 인증: serviceKey (KCISA에서 발급)
    
    [요청 파라미터]
    - serviceKey   (string, 필수)  : KCISA API 키
    - numOfRows    (string, 선택)  : 세션당 요청 레코드 수
    - pageNo       (string, 선택)  : 페이지 수
    - title        (string, 선택)  : 검색어(제목)
    
    [출력값 - 샘플 코드 기준]
    1. TITLE                  : 제목
    2. URL                    : URL
    3. DESCRIPTION            : 소개(설명)
    4. LOCAL_ID               : ID
    5. AGENCY_CATEGORY_TYPE   : 기관분류코드
    6. FORMAT                 : 자료형식
    7. LANGUAGE               : 언어
    8. UCI                    : UCI
    9. CULTURAL_HERITAGE_AGENT: 전문가단체
    10. ISSUED_DATE           : 자료생성일자
    11. IMAGE_OBJECT          : 이미지주소  ← 이미지 URL 후보
    12. SOURCE_TITLE          : 참조자원제목
    13. ISBN                  : ISBN
    14. CREATED_DATE          : 창작일
    15. VIDEO_OBJECT          : 동영상URL
    16. SUB_DESCRIPTION       : 부가설명
    17. CNTC_INSTT_NM         : 제공기관명
    """
    KCISA_KEY = os.getenv("KCISA_API_KEY", "")
    if not KCISA_KEY:
        print("[PublicData] KCISA_API_KEY 미설정 (.env 확인)")
        return None
    
    url = "https://api.kcisa.kr/openapi/API_CIA_092/request"
    params = {
        "serviceKey": KCISA_KEY,
        "numOfRows": "20",
        "pageNo": "1",
    }
    if keyword:
        params["title"] = keyword
    
    # --- HTTP 요청 ---
    try:
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            resp = await client.get(url, params=params)
            print(f"[PublicData] KCISA HTTP Status: {resp.status_code}")
            print(f"[PublicData] KCISA 요청 URL: {resp.url}")
            
            if resp.status_code == 401:
                print("[PublicData] KCISA 401 Unauthorized - API 키가 유효하지 않거나 해당 서비스 이용 신청이 필요합니다")
                return None
            if resp.status_code == 403:
                print("[PublicData] KCISA 403 Forbidden - 이용 권한이 없습니다")
                return None
            if resp.status_code == 504:
                print("[PublicData] KCISA 504 Gateway Timeout - KCISA 서버 장애")
                return None
            if resp.status_code != 200:
                print(f"[PublicData] KCISA 오류 응답: {resp.text[:500]}")
                return None
            
            resp_text = resp.text
    except Exception as e:
        print(f"[PublicData] KCISA 요청 예외: {type(e).__name__}: {e}")
        return None
    
    # --- XML 파싱 ---
    try:
        root = ET.fromstring(resp_text)
    except ET.ParseError as e:
        print(f"[PublicData] KCISA XML 파싱 오류: {e}")
        print(f"[PublicData] 원본 응답 일부: {resp_text[:300]}")
        return None
    
    # --- 결과 코드 확인 ---
    result_code = root.find(".//resultCode")
    result_msg = root.find(".//resultMsg")
    
    if result_code is not None:
        print(f"[PublicData] KCISA resultCode: {result_code.text}")
    if result_msg is not None:
        print(f"[PublicData] KCISA resultMsg: {result_msg.text}")
    
    if result_code is None or result_code.text != "00":
        msg = result_msg.text if result_msg is not None else "Unknown"
        print(f"[PublicData] KCISA API 결과 오류: {msg}")
        return None
    
    # --- 아이템 추출 ---
    items = root.findall(".//item")
    print(f"[PublicData] KCISA item 개수: {len(items)}")
    if not items:
        return None
    
    candidates = []
    for item in items[:10]:
        # 샘플 코드 기준 - 대문자 태그명
        title = item.findtext("TITLE", default="")
        description = item.findtext("DESCRIPTION", default="")
        url_field = item.findtext("URL", default="")
        image_object = item.findtext("IMAGE_OBJECT", default="")
        local_id = item.findtext("LOCAL_ID", default="")
        agency_type = item.findtext("AGENCY_CATEGORY_TYPE", default="")
        fmt = item.findtext("FORMAT", default="")
        language = item.findtext("LANGUAGE", default="")
        uci = item.findtext("UCI", default="")
        heritage_agent = item.findtext("CULTURAL_HERITAGE_AGENT", default="")
        issued_date = item.findtext("ISSUED_DATE", default="")
        source_title = item.findtext("SOURCE_TITLE", default="")
        isbn = item.findtext("ISBN", default="")
        created_date = item.findtext("CREATED_DATE", default="")
        video_object = item.findtext("VIDEO_OBJECT", default="")
        sub_description = item.findtext("SUB_DESCRIPTION", default="")
        cntc_instt = item.findtext("CNTC_INSTT_NM", default="")
        
        # 이미지 URL 후보: IMAGE_OBJECT 우선, 없으면 URL
        media_url = None
        if image_object and image_object.startswith("http"):
            media_url = image_object
            print(f"[PublicData] KCISA IMAGE_OBJECT 발견: {media_url[:100]}")
        elif url_field and url_field.startswith("http"):
            media_url = url_field
            print(f"[PublicData] KCISA URL 발견: {media_url[:100]}")
        
        candidates.append({
            "title": title,
            "description": description or sub_description,
            "media_url": media_url,
            "media_type": "image",
            "source": cntc_instt or "국립민속박물관",
            "source_url": url_field or "https://www.nfm.go.kr",
            "text_content": None,
            # 메타데이터 (디버깅/추가 정보용)
            "local_id": local_id,
            "agency_category_type": agency_type,
            "format": fmt,
            "language": language,
            "uci": uci,
            "cultural_heritage_agent": heritage_agent,
            "issued_date": issued_date,
            "source_title": source_title,
            "isbn": isbn,
            "created_date": created_date,
            "video_object": video_object,
            "sub_description": sub_description,
        })
    
    print(f"[PublicData] KCISA 후보 {len(candidates)}개 추출 완료")
    return candidates


async def fetch_archives(keyword: str = "") -> list[dict] | None:
    """
    공공데이터포털 - 국가기록원 나라기록물정보 API
    
    [확정된 엔드포인트]
    - https://apis.data.go.kr/1741050/openapi/searcharc
    
    [요청 파라미터]
    - serviceKey   (string, 필수) : 공공데이터포털 인증키 (URL 인코딩된 키)
    - pageNo       (int,    선택) : 페이지 번호 (기본값 1)
    - query        (string, 선택) : 검색어 (기존 searchKeyword 아님!)
    - rc_type      (string, 선택) : 기록물 유형 - rfile(기록물)
    - display      (int,    선택) : 한 페이지 결과 수 (기존 numOfRows 아님!)
    
    [응답 구조 - RSS 2.0 XML]
    <rss>
      <channel>
        <title>...</title>
        <total>전체 결과 수</total>
        <item>
          <rc_type>RFILE</rc_type>
          <rc_code>1310377</rc_code>
          <rc_rfile_no>201103733609</rc_rfile_no>
          <rc_ritem_no />               (하위 항목 번호, 없을 수 있음)
          <title>기록물 제목</title>
          <mgt_org_name>국가기록원</mgt_org_name>
          <prod_name>생산자명</prod_name>
          <prod_year>2008</prod_year>
          <is_open>1</is_open>           (1=공개, 2=비공개)
          <arcave_type>05</arcave_type>
          <doc_type>M</doc_type>         (M=영상, D=문서, A=사진 등)
          <online_reading>N</online_reading>
          <link>상세페이지 URL</link>
        </item>
      </channel>
    </rss>
    
    ⚠️ 응답에 이미지/썸네일 URL 필드가 없음. 
       기록물 상세 링크(<link>)만 제공됨.
       이미지가 필요하면 <link> 상세페이지를 파싱하거나,
       rc_type을 변경하여 사진 자료만 필터링해야 할 수 있음.
    """
    if not settings.public_data_api_key:
        print("[PublicData] PUBLIC_DATA_API_KEY 미설정 (.env 확인)")
        return None
    
    url = "https://apis.data.go.kr/1741050/openapi/searcharc"
    params = {
        "serviceKey": settings.public_data_api_key,
        "pageNo": "1",
        "display": "20",
        "rc_type": "rfile",
    }
    if keyword:
        params["query"] = keyword
    
    # --- HTTP 요청 ---
    try:
        async with httpx.AsyncClient(timeout=8, verify=False) as client:
            resp = await client.get(url, params=params)
            print(f"[PublicData] Archives HTTP Status: {resp.status_code}")
            print(f"[PublicData] Archives 요청 URL: {resp.url}")
            
            if resp.status_code == 401:
                print("[PublicData] Archives 401 - 인증키가 유효하지 않습니다")
                return []
            if resp.status_code == 403:
                print("[PublicData] Archives 403 - 이용 권한이 없습니다 (이용 신청 필요)")
                return []
            if resp.status_code == 500:
                print("[PublicData] Archives 500 - 서버 내부 오류")
                return []
            if resp.status_code != 200:
                print(f"[PublicData] Archives 오류 응답: {resp.text[:500]}")
                return []
            
            resp_text = resp.text
    except Exception as e:
        print(f"[PublicData] Archives 요청 예외: {type(e).__name__}: {e}")
        return []
    
    # --- XML 파싱 (RSS 2.0) ---
    try:
        root = ET.fromstring(resp_text)
    except ET.ParseError as e:
        print(f"[PublicData] Archives XML 파싱 오류: {e}")
        print(f"[PublicData] 원본 응답 일부: {resp_text[:300]}")
        return None
    
    # --- 전체 결과 수 확인 ---
    total = root.find(".//total")
    if total is not None:
        print(f"[PublicData] Archives 전체 결과 수: {total.text}")
    
    # --- 아이템 추출 ---
    items = root.findall(".//item")
    print(f"[PublicData] Archives item 개수: {len(items)}")
    if not items:
        return None
    
    candidates = []
    for item in items[:10]:
        title = item.findtext("title", default="")
        
        # 기록물 상세 페이지 링크
        detail_link = item.findtext("link", default="")
        
        # 생산자/기관 정보
        prod_name = item.findtext("prod_name", default="")
        mgt_org = item.findtext("mgt_org_name", default="국가기록원")
        prod_year = item.findtext("prod_year", default="")
        doc_type = item.findtext("doc_type", default="")
        
        # 설명 구성
        description = ""
        if prod_name:
            description += f"생산자: {prod_name}. "
        if prod_year:
            description += f"생산연도: {prod_year}. "
        if doc_type:
            description += f"문서유형: {doc_type}."
        
        # ⚠️ 이 API 응답에는 이미지 URL 필드가 없음!
        # media_url은 None으로 설정하고, source_url에 상세페이지 링크 제공
        media_url = None
        
        # 이 API는 기록물(이야기/문서) 메타데이터이므로 media_type=text
        candidates.append({
            "title": title,
            "description": description,
            "media_url": None,
            "media_type": "text",  # 기록물은 text 타입
            "source": mgt_org,
            "source_url": detail_link or "https://www.archives.go.kr",
            "text_content": None,  # 상세 페이지 본문은 별도 파싱 필요
            # 추가 메타데이터
            "rc_code": item.findtext("rc_code", default=""),
            "rc_rfile_no": item.findtext("rc_rfile_no", default=""),
            "prod_year": prod_year,
            "doc_type": doc_type,
            "is_open": item.findtext("is_open", default=""),
        })
    
    print(f"[PublicData] Archives 후보 {len(candidates)}개 추출 완료 (이미지 URL 없음)")
    return candidates


async def validate_media_url(url: str | None) -> str | None:
    """URL HEAD 요청으로 접근 가능 여부 확인"""
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=5, verify=False) as client:
            resp = await client.head(url, follow_redirects=True)
            return url if resp.status_code == 200 else None
    except Exception:
        return None


async def cache_media(url: str, media_type: str) -> str:
    """미디어 파일을 로컬에 캐시하고 서빙 가능한 경로 반환"""
    cache_dir = settings.media_cache_dir
    os.makedirs(cache_dir, exist_ok=True)
    
    ext_map = {"image": "jpg", "audio": "mp3", "video": "mp4", "text": "txt"}
    ext = ext_map.get(media_type, "bin")
    
    filename = hashlib.md5(url.encode()).hexdigest() + f".{ext}"
    local_path = os.path.join(cache_dir, filename)
    
    if not os.path.exists(local_path):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            async with aiofiles.open(local_path, "wb") as f:
                await f.write(resp.content)
        except Exception as e:
            print(f"[PublicData] 미디어 캐시 실패: {url} - {e}")
            raise
    
    return f"/media/{filename}"


async def refine_topic_question(
    topic_title: str,
    current_question_set: QuestionSet,
    instruction: str,
) -> QuestionSet:
    """
    기존 설문지를 복지사의 자연어 수정 요청에 따라 개선합니다.
    API 키가 없거나 실패하면 기존 QuestionSet을 그대로 반환합니다.
    """
    template_path = PROMPT_DIR / "topic_refine_v1.txt"
    if not template_path.exists():
        return current_question_set

    template = template_path.read_text(encoding="utf-8")
    prompt = template.format(
        topic_title=topic_title,
        current_question_set_json=current_question_set.model_dump_json(ensure_ascii=False, indent=2),
        instruction=instruction,
    )

    result = await _generate_with_opencode(prompt)
    if result:
        return result

    print("[PublicData] OpenCode refine 실패, 원본 반환")
    return current_question_set


def _build_fallback_question_set(
    question_type: str,
    title: str = "이 주제",
    question_count: int = 1,
    narrative_count: int = 1,
    choice_count: int = 1,
) -> QuestionSet:
    """
    AI API 실패 시, 지정한 수량만큼 기본 질문을 동적으로 생성하여 반환.
    """
    from copy import deepcopy

    # 총 질문 수 계산
    total = question_count
    if question_type == "mixed":
        total = choice_count + narrative_count

    base_questions = []

    if question_type == "narrative":
        # 서술형 폴백 템플릿
        templates = [
            "{title}에 대해 어떤 기억이 떠오르세요?",
            "{title}과 관련해 특별했던 순간을 이야기해 주세요.",
            "{title}을(를) 생각하면 어떤 감정이 드시나요?",
            "{title}에 대한 이야기를 자유롭게 나눠 주세요.",
            "{title}을(를) 경험했던 때를 떠올려 보세요.",
        ]
        for i in range(total):
            tpl = templates[i % len(templates)]
            base_questions.append(
                QuestionItem(
                    id=f"q{i+1}",
                    type="narrative",
                    text=tpl.format(title=title),
                    target_age="elderly",
                    placeholder="자유롭게 이야기해 주세요...",
                    guidelines=["떠오르는 대로", "구체적인 장면을"],
                    suggested_duration_seconds=45,
                )
            )

    elif question_type == "choice":
        # 선택형 폴백 템플릿
        templates = [
            "{title}에 대해 어떤 생각이 드시나요?",
            "{title}과 관련해 가장 기억에 남는 것은 무엇인가요?",
            "{title}을(를) 경험한 적이 있으신가요?",
            "{title}에 대해 가장 먼저 떠오르는 것은 무엇인가요?",
            "{title}과(와) 관련해 어떤 감정을 느끼시나요?",
        ]
        for i in range(total):
            tpl = templates[i % len(templates)]
            base_questions.append(
                QuestionItem(
                    id=f"q{i+1}",
                    type="choice",
                    text=tpl.format(title=title),
                    target_age="elderly",
                    allow_multiple=False,
                    has_other=True,
                    options=[
                        ChoiceOption(id=f"opt_{i}_1", label="네, 많이 경험했어요", value="A", icon_hint="🙂"),
                        ChoiceOption(id=f"opt_{i}_2", label="가끔 생각나요", value="B", icon_hint="🤔"),
                        ChoiceOption(id=f"opt_{i}_3", label="잘 모르겠어요", value="C", icon_hint="😊"),
                        ChoiceOption(id=f"opt_{i}_other", label="기타 (직접 말씀해 주세요)", value="OTHER", is_other=True),
                    ],
                )
            )

    elif question_type == "mixed":
        # 혼합형: choice_count개 + narrative_count개
        choice_templates = [
            "{title}에 대해 경험이 있으신가요?",
            "{title}과(와) 관련해 가장 기억에 남는 것은 무엇인가요?",
        ]
        narrative_templates = [
            "{title}에 대한 이야기를 자세히 들려주세요.",
            "{title}을(를) 생각하면 어떤 장면이 떠오르세요?",
        ]
        # 선택형
        for i in range(choice_count):
            tpl = choice_templates[i % len(choice_templates)]
            base_questions.append(
                QuestionItem(
                    id=f"q{i+1}",
                    type="choice",
                    text=tpl.format(title=title),
                    target_age="elderly",
                    allow_multiple=False,
                    has_other=True,
                    options=[
                        ChoiceOption(id=f"opt_{i}_1", label="네, 많이 경험했어요", value="A", icon_hint="🙂"),
                        ChoiceOption(id=f"opt_{i}_2", label="가끔 생각나요", value="B", icon_hint="🤔"),
                        ChoiceOption(id=f"opt_{i}_3", label="잘 모르겠어요", value="C", icon_hint="😊"),
                        ChoiceOption(id=f"opt_{i}_other", label="기타 (직접 말씀해 주세요)", value="OTHER", is_other=True),
                    ],
                )
            )
        # 서술형
        for i in range(narrative_count):
            tpl = narrative_templates[i % len(narrative_templates)]
            base_questions.append(
                QuestionItem(
                    id=f"q{choice_count + i + 1}",
                    type="narrative",
                    text=tpl.format(title=title),
                    target_age="elderly",
                    placeholder="자유롭게 이야기해 주세요...",
                    guidelines=["떠오르는 대로", "구체적인 장면을"],
                    suggested_duration_seconds=45,
                )
            )

    return QuestionSet(
        schema_version="1.0",
        question_type=question_type,
        questions=base_questions,
    )


async def generate_topic_question(
    title: str,
    description: str,
    media_type: str,
    target_age: str,
    question_type: str,
    custom_hint: str = "",
    question_count: int = 1,
    narrative_count: int = 1,
    choice_count: int = 1,
) -> QuestionSet:
    """
    딥시크 API로 대화 유도 질문을 instructor + Pydantic 스키마로 강제 생성.
    Returns: QuestionSet
    """
    template_path = PROMPT_DIR / f"topic_publish_{question_type}_v1.txt"
    if not template_path.exists():
        return DEFAULT_FALLBACK

    template = template_path.read_text(encoding="utf-8")
    prompt = template.format(
        title=title,
        description=description or "",
        media_type=media_type,
        target_age=target_age,
        custom_hint=custom_hint or "",
        question_count=question_count,
        narrative_count=narrative_count,
        choice_count=choice_count,
        total_count=choice_count + narrative_count,
    )
    print(f"[PublicData] 질문 생성 요청: type={question_type}, count={question_count}, narrative={narrative_count}, choice={choice_count}")

    result = await _generate_with_opencode(prompt)
    if result:
        return result

    print("[PublicData] AI 생성 실패 - 폴백 질문 사용")
    return _build_fallback_question_set(question_type, title, question_count, narrative_count, choice_count)


async def save_weekly_topic(db: AsyncSession, topic_data: dict) -> WeeklyTopic:
    """새 주제를 weekly_topics 테이블에 저장"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    # 이번 주 해당 지역 주제가 이미 있으면 업데이트
    existing = await db.execute(
        select(WeeklyTopic).where(
            WeeklyTopic.active_week == monday,
            WeeklyTopic.region == topic_data.get("region", "default"),
        )
    )
    topic = existing.scalar_one_or_none()
    
    if topic is None:
        topic = WeeklyTopic(
            active_week=monday,
            region=topic_data.get("region", "default"),
        )
        db.add(topic)
    
    topic.title = topic_data["title"]
    topic.description = topic_data.get("description", "")
    topic.media_url = topic_data.get("media_url")
    topic.media_type = topic_data.get("media_type", "text")
    topic.source = topic_data.get("source", "")
    topic.source_url = topic_data.get("source_url", "")
    topic.ai_question = topic_data.get("ai_question", "")
    topic.text_content = topic_data.get("text_content")
    topic.welfare_id = topic_data.get("welfare_id")
    topic.question_type = topic_data.get("question_type", "narrative")
    topic.is_customized = topic_data.get("is_customized", False)
    topic.parent_topic_id = topic_data.get("parent_topic_id")
    topic.duration_seconds = topic_data.get("duration_seconds")
    
    choices = topic_data.get("choices")
    if choices is not None:
        if isinstance(choices, QuestionSet):
            topic.choices = choices.model_dump_json(ensure_ascii=False)
        elif isinstance(choices, dict):
            topic.choices = json.dumps(choices, ensure_ascii=False)
        elif isinstance(choices, list):
            topic.choices = json.dumps(choices, ensure_ascii=False)
        else:
            topic.choices = str(choices)
    else:
        topic.choices = None
    
    await db.commit()
    await db.refresh(topic)
    return topic


async def get_active_topic(
    db: AsyncSession,
    region: str = "default",
) -> dict:
    """이번 주 활성 주제: DB 우선 (지역 기준), 없으면 TOPIC_POOL 폴백"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    # 1. 해당 지역의 주제 우선 조회
    result = await db.execute(
        select(WeeklyTopic).where(
            WeeklyTopic.active_week == monday,
            WeeklyTopic.region == region,
        )
        .order_by(WeeklyTopic.is_customized.desc())
    )
    topic = result.scalar_one_or_none()
    
    # 2. 해당 지역에 없으면 중앙 기본 주제 조회
    if not topic:
        result = await db.execute(
            select(WeeklyTopic).where(
                WeeklyTopic.active_week == monday,
                WeeklyTopic.region == "default",
            )
        )
        topic = result.scalar_one_or_none()
    
    # 3. DB에 있으면 반환
    if topic:
        choices = None
        if topic.choices and topic.choices not in ("null", "None", ""):
            try:
                raw = json.loads(topic.choices)
                # 새 구조 (dict) vs 구 구조 (list) 판별
                if isinstance(raw, dict) and raw.get("schema_version") == "1.0":
                    choices = raw
                elif isinstance(raw, list):
                    choices = raw
            except Exception:
                choices = None
        
        # ai_question 폴백: choices 신구조에서 첫 질문 text 사용
        ai_question = topic.ai_question
        if not ai_question and isinstance(choices, dict) and choices.get("questions"):
            ai_question = choices["questions"][0].get("text", "")
        
        return {
            "id": str(topic.id),
            "title": topic.title,
            "description": topic.description,
            "media_url": topic.media_url,
            "media_type": topic.media_type,
            "source": topic.source,
            "source_url": topic.source_url,
            "ai_question": ai_question,
            "text_content": topic.text_content,
            "question_type": topic.question_type,
            "choices": choices,
            "active_week": topic.active_week.isoformat() if topic.active_week else None,
            "region": topic.region,
        }
    
    # 4. 폴백: text 샘플 우선 (image 비활성화)
    text_pool = [t for t in TOPIC_POOL if t["media_type"] == "text"]
    pool = text_pool if text_pool else TOPIC_POOL
    idx = monday.isocalendar().week % len(pool)
    topic = pool[idx].copy()
    topic["id"] = None
    topic["active_week"] = monday.isoformat()
    topic["media_url"] = None
    topic["region"] = region
    return topic


BLACKLIST_KEYWORDS = [
    "밀수", "단속", "적발", "범죄", "사고", "화재", "재해", "재난",
    "코로나", "감염", "방역", "집단", "폭발", "폭행", "살인", "사망",
    "위험", "경고", "금지", "조사", "수사", "기소", "처벌", "벌금",
    "형사", "형벌", "교도소", "구속", "체포", "검거", "소송", "소추",
    "고발", "신고", "단금", "적발", "연구", "보고서", "정책", "활성화 방안",
    "의원", "연구단체", "연구회", "발전 방안", "대책", "계획", "추진",
]


async def _is_topic_emotionally_suitable(title: str, description: str = "") -> bool:
    """
    AI를 통해 주제가 세대공감 대화에 감성적으로 적합한지 판단.
    정책 연구, 보고서, 학술 자료 등은 거짓(False)을 반환.
    """
    # 1. 블랙리스트 빠른 필터
    full_text = f"{title} {description}".lower()
    for bad in BLACKLIST_KEYWORDS:
        if bad.lower() in full_text:
            print(f"[PublicData] 블랙리스트 차단: '{bad}' in '{title[:40]}...'")
            return False

    # AI 감성 판단은 속도 문제로 생략. 블랙리스트만으로 필터링.
    return True


async def search_topic_candidates(
    media_type: str,
    keyword: str = "",
    quantity: int = 3,
) -> list[dict]:
    """
    공공 API에서 후보 검색 (미디어 타입 + 키워드 기반)
    
    [흐름]
    1. media_type == "image"  → KCISA(민속박물관) + 공공데이터포털(국가기록원) 병렬 호출
    2. media_type == "text"   → TOPIC_POOL 샘플에서 직접 선택
    3. media_type == "audio"  → TOPIC_POOL 샘플에서 직접 선택
    4. API 결과 부족 시      → TOPIC_POOL 샘플로 보충
    
    [주의]
    - image 타입: API 성공 시 이미지를 로컬 캐시(cache_media) 후 /media/ 경로 반환
    - API 실패(401, 403, 500, 타임아웃) 시 자동으로 샘플 폴백
    """
    import asyncio
    candidates = []

    if media_type == "image":
        print("[PublicData] image 타입은 현재 비활성화되어 있습니다. 후보를 반환하지 않습니다.")
        # image 타입 완전 비활성화: API 호출 없음, 샘플도 사용 안 함

    elif media_type == "text":
        # 공공 API 호출 생략, TOPIC_POOL 샘플 직접 사용 (속도 개선 및 안정성)
        print(f"[PublicData] 텍스트 후보: TOPIC_POOL 샘플 직접 사용 (quantity={quantity})")
        text_samples = [t for t in TOPIC_POOL if t["media_type"] == "text"]
        already_titles: set[str] = set()
        for s in random.sample(text_samples, min(quantity, len(text_samples))):
            if len(candidates) >= quantity:
                break
            if s["title"] not in already_titles:
                sc = s.copy()
                if not sc.get("question_type"):
                    sc["question_type"] = "narrative"
                candidates.append(sc)
                already_titles.add(s["title"])
                print(f"[PublicData] 후보 추가(샘플): {sc['title'][:40]}...")

    elif media_type == "audio":
        print(f"[PublicData] 오디오 후보 검색 - TOPIC_POOL 샘플 사용")
        audio_samples = [t for t in TOPIC_POOL if t["media_type"] == "audio"]
        for s in random.sample(audio_samples, min(quantity, len(audio_samples))):
            sc = s.copy()
            if not sc.get("question_type"):
                sc["question_type"] = "choice"
            candidates.append(sc)

    # ── 부족분을 TOPIC_POOL 샘플로 채움 (image 제외) ──
    if len(candidates) < quantity and media_type != "image":
        short = quantity - len(candidates)
        print(f"[PublicData] API 결과 부족 ({len(candidates)}/{quantity}) - 샘플 {short}개 보충")
        pool = [t for t in TOPIC_POOL if t["media_type"] == media_type]
        already_titles = {c["title"] for c in candidates}
        for s in random.sample(pool, min(len(pool), short)):
            if len(candidates) >= quantity:
                break
            if s["title"] not in already_titles:
                sc = s.copy()
                if not sc.get("question_type"):
                    if media_type == "text":
                        sc["question_type"] = "narrative"
                    elif media_type == "audio":
                        sc["question_type"] = "choice"
                candidates.append(sc)
                already_titles.add(s["title"])
                print(f"[PublicData] 샘플 보충: {s['title'][:40]}...")

    print(f"[PublicData] 최종 후보: {len(candidates)}개 (요청: {quantity})")
    return candidates[:quantity]


# --- APScheduler용 주간 자동 발행 ---

KEYWORD_POOL = [
    "전통 시장", "명절", "민요", "설화", "농촌",
    "학교", "동네", "가족", "장터", "고향",
]


async def publish_weekly_default_topic():
    """매주 월요일 00:00 - 중앙 기본 주제 자동 생성"""
    import logging
    logger = logging.getLogger("ium.scheduler")
    
    keyword = random.choice(KEYWORD_POOL)
    # image 타입 비활성화 -> text 타입으로 검색
    candidates = await search_topic_candidates("text", keyword, quantity=1)
    
    if not candidates:
        # API 완전 실패 시 text 샘플에서 무작위 선택
        text_samples = [t for t in TOPIC_POOL if t["media_type"] == "text"]
        candidates = [random.choice(text_samples) if text_samples else TOPIC_POOL[0]]
    
    topic_data = candidates[0]
    topic_data["region"] = "default"
    topic_data["welfare_id"] = None
    topic_data["is_customized"] = False
    topic_data["question_type"] = "narrative"
    
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await save_weekly_topic(db, topic_data)
    
    logger.info(f"[Scheduler] 중앙 기본 주제 발행: {topic_data['title']}")


async def remind_pending_welfare_workers():
    """월요일 09:00 - 미발행 관리자 리마인더"""
    import logging
    logger = logging.getLogger("ium.scheduler")
    
    from app.database import AsyncSessionLocal
    from app.models.models import WelfareWorker, WeeklyTopic
    
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    async with AsyncSessionLocal() as db:
        published = await db.execute(
            select(WeeklyTopic.welfare_id)
            .where(
                WeeklyTopic.active_week == monday,
                WeeklyTopic.is_customized == True,
            )
            .distinct()
        )
        published_ids = {row[0] for row in published.all()}
        
        all_workers = await db.execute(select(WelfareWorker))
        for w in all_workers.scalars().all():
            if w.id not in published_ids:
                logger.warning(f"[Reminder] 관리자 {w.name}({w.region}) 미발행")
                # TODO: 실제 알림 전송 (Push, 이메일, SMS)


async def emergency_publish_by_admin():
    """수요일 00:00 - 미발행 지역에 중앙 주제 복제"""
    import logging
    logger = logging.getLogger("ium.scheduler")
    
    from app.database import AsyncSessionLocal
    from app.models.models import WelfareWorker, WeeklyTopic
    
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    async with AsyncSessionLocal() as db:
        published = await db.execute(
            select(WeeklyTopic.welfare_id)
            .where(
                WeeklyTopic.active_week == monday,
                WeeklyTopic.is_customized == True,
            )
            .distinct()
        )
        published_ids = {row[0] for row in published.all()}
        
        all_workers = await db.execute(select(WelfareWorker))
        for w in all_workers.scalars().all():
            if w.id not in published_ids:
                base_topic = await db.execute(
                    select(WeeklyTopic).where(
                        WeeklyTopic.active_week == monday,
                        WeeklyTopic.region == "default",
                    )
                )
                base = base_topic.scalar_one_or_none()
                if base:
                    emergency = WeeklyTopic(
                        title=base.title,
                        description=base.description,
                        media_url=base.media_url,
                        media_type=base.media_type,
                        source=base.source,
                        source_url=base.source_url,
                        ai_question=base.ai_question,
                        text_content=base.text_content,
                        active_week=monday,
                        region=w.region,
                        welfare_id=None,
                        question_type=base.question_type,
                        is_customized=False,
                        parent_topic_id=base.id,
                    )
                    db.add(emergency)
                    logger.warning(f"[Emergency] {w.region} 임시 발행: {base.title}")
        
        await db.commit()
