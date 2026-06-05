# Pipeline A — 주제 선정 상세 구현 계획 (복지사 중심 · 지역 기반)

> **핵심 철학**: AI는 조수, 복지사가 주인공. 복지사가 담당 지역의 노인과 청년을 위해 직접 주제를 선택·발행한다.
> **의존**: 없음 (최우선 파이프라인)
> **영향**: B(주제 전달), D(수필 주제), C(주제별 감정 집계)
> **작성 기준일**: 2026년 6월 1일

---

## 1. 현재 코드 상태 (진단)

| 파일 | 현재 상태 | 문제 |
|---|---|---|
| `backend/app/services/public_data.py` | `TOPIC_POOL` 5개 하드코딩 | 공공 API 0% 연동 |
| `public_data.py:51-60` | `get_active_topic()` — DB 미조회, 산술 인덱싱 | 새 주제 추가 불가 |
| `public_data.py:63-79` | `fetch_from_archives_api()` — 정의만 존재, 호출 없음 | 실 데이터 수집 불가 |
| `models/models.py:37-51` | `WeeklyTopic` 테이블 스키마 완성 | `region`, `question_type`, `welfare_id` 등 누락 |
| `backend/app/main.py` | APScheduler 없음 | 자동 발행 불가 |

---

## 2. 서비스 설계 원칙

### 2-1. 역할 분리

| 역할 | 주인공 / 조수 | 설명 |
|---|---|---|
| **복지사** | **주인공** | 담당 지역 사용자에게 주제를 선택·발행하는 결정권자 |
| **AI** | **조수** | 공공데이터 검색, 후보 조합, 질문 생성 등을 지원 |
| **중앙 관리자** | **감독자** | 복지사 미발행 시 임시 발행, 정책 수준 조정 |

### 2-2. 핵심 흐름

```
[월요일 00:00] AI가 중앙 기본 주제 자동 생성 (공공데이터 기반)
    ↓
[복지사 대시보드] "이번 주 기본 주제: 1960년대 남대문 시장"
                + [지역 특화 적용] 버튼
    ↓
[복지사 선택]
  ├─ [적용 안 함] → 중앙 주제 그대로 (region = "default")
  ├─ [간단 협의] → 카테고리/감정/지역 선택 → AI 후보 3개 → 복지사 1개 선택 → 질문 유형 선택
  └─ [상세 협의] → 자연어로 AI와 대화 → 주제 구성 → 질문 유형 선택
    ↓
[weekly_topics] DB 저장 (region, welfare_id, question_type, is_customized)
    ↓
[사용자 앱] 해당 지역 노인/청년에게 주제 + 구성된 질문 노출
```

### 2-3. 미발행 Fallback (C + D)

| 시간 | 조치 | 주체 |
|---|---|---|
| 월요일 00:00 | AI가 중앙 기본 주제 자동 생성 | 시스템 |
| 월요일 09:00 | 복지사 미발행 시 **리마인더 알림** (Push/이메일/대시보드 배너) | 시스템 → 복지사 |
| 수요일 00:00 | 복지사가 여전히 미발행 → **상위 복지기관(중앙 관리자) 임시 발행** | 중앙 관리자 |

> **중요**: 복지사가 "미적용(중앙 주제 그대로)"을 선택한 것은 "발행"으로 간주. 리마인더는 복지사가 아무 행동도 취하지 않은 경우에만 발송.

---

## 3. 구현 목표 (단계별)

```
[Step 1] DB 스키마 확장
         weekly_topics 테이블에 region, welfare_id, question_type, is_customized 추가
         새 테이블: topic_proposals (복지사-AI 협의 이력)

[Step 2] 공공 API 클라이언트 구현
         국가기록원(이미지) / 국립민속박물관(설화·이미지) / 국립국악원(음원)

[Step 3] 미디어(비정형 데이터) 파싱 · 캐싱 · 서빙
         image / audio / video / text 4가지 타입 처리
         로컬 캐시 + StaticFiles 서빙

[Step 4] 복지사 듀얼 협의 시스템
         상세 협의(자연어 대화) + 간단 협의(폼/위저드)
         복지사가 주제 및 질문 유형(선택형/서술형/혼합형) 선택

[Step 5] 지역 기반 주제 배분
         get_active_topic() → region 기준 필터링
         복지사 대시보드 → 지역별 주제 발행 UI

[Step 6] APScheduler 자동 발행 + 미발행 Fallback
         매주 월요일 중앙 기본 주제 생성
         리마인더 알림 + 상위 기관 임시 발행
```

---

## 4. Step 1 — DB 스키마 확장

### 4-1. weekly_topics 테이블 수정

**파일**: `backend/init.sql`

```sql
-- 기존 weekly_topics 테이블에 컬럼 추가
ALTER TABLE weekly_topics ADD COLUMN region VARCHAR(100) DEFAULT 'default';
ALTER TABLE weekly_topics ADD COLUMN welfare_id UUID REFERENCES welfare_workers(id);
ALTER TABLE weekly_topics ADD COLUMN question_type VARCHAR(20) DEFAULT 'narrative';
  -- 'choice' | 'narrative' | 'mixed'
ALTER TABLE weekly_topics ADD COLUMN is_customized BOOLEAN DEFAULT FALSE;
  -- TRUE: 복지사가 지역 특화 적용한 주제
  -- FALSE: 중앙 기본 주제 그대로
ALTER TABLE weekly_topics ADD COLUMN parent_topic_id UUID REFERENCES weekly_topics(id);
  -- 중앙 기본 주제 참조 (지역 특화 주제가 어떤 기본 주제에서 파생되었는지)
ALTER TABLE weekly_topics ADD COLUMN text_content TEXT;
  -- media_type='text'일 때 설화/이야기 본문 저장
ALTER TABLE weekly_topics ADD COLUMN preview_thumbnail TEXT;
  -- 썸네일 URL (이미지/비디오용)
ALTER TABLE weekly_topics ADD COLUMN duration_seconds INT;
  -- 오디오/비디오 길이 (선택)
```

### 4-2. 새 테이블: topic_proposals (복지사-AI 협의 이력)

```sql
CREATE TABLE topic_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    welfare_id UUID REFERENCES welfare_workers(id),
    mode VARCHAR(20) NOT NULL,              -- 'detailed' | 'simple'
    welfare_input TEXT,                    -- 복지사 의도/선택 내용
    ai_suggestions JSONB,                    -- AI 제안 후보 목록
    welfare_selection UUID,                -- 복지사 최종 선택 (weekly_topics.id 참조)
    question_type VARCHAR(20),             -- 'choice' | 'narrative' | 'mixed'
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending' | 'approved' | 'rejected'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. Step 2 — 공공 API 클라이언트

### 5-1. 환경변수 추가

**파일**: `backend/app/config.py`

```python
# 기존 public_data_api_key 대신 3개 기관 키로 분리
archives_api_key: str = ""          # 국가기록원
folk_museum_api_key: str = ""       # 국립민속박물관
gugak_api_key: str = ""             # 국립국악원

# 미디어 캐시
media_cache_dir: str = "/tmp/ium_media"
```

**파일**: `.env.example`

```
# 공공데이터 API 키
ARCHIVES_API_KEY=your_archives_api_key
FOLK_MUSEUM_API_KEY=your_folk_museum_api_key
GUGAK_API_KEY=your_gugak_api_key
```

### 5-2. API 클라이언트 구현

**파일**: `backend/app/services/public_data.py`

#### 국가기록원 (이미지/문서)

- API: `https://www.archives.go.kr/next/api/searchRecords.do`
- 파라미터: `systemId`, `keyword`, `pageSize=10`, `pageNum=1`
- 응답 파싱: `result.list[].thumbnailUrl`, `result.list[].title`, `result.list[].id`
- **미디어 타입**: `image`

```python
async def fetch_archives(keyword: str) -> dict | None:
    """국가기록원 이미지 검색"""
    if not settings.archives_api_key:
        return None
    url = "https://www.archives.go.kr/next/api/searchRecords.do"
    params = {
        "systemId": settings.archives_api_key,
        "keyword": keyword,
        "pageSize": 10,
        "pageNum": 1,
        "sortOrder": "RELEVANCE",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
    items = resp.json().get("result", {}).get("list", [])
    if not items:
        return None
    item = random.choice(items[:5])
    return {
        "title": item.get("title", ""),
        "description": item.get("description", ""),
        "media_url": item.get("thumbnailUrl"),
        "media_type": "image",
        "source": "국가기록원",
        "source_url": f"https://www.archives.go.kr/next/content/listSubjectDescription.do?id={item.get('id','')}",
        "text_content": None,  # 이미지 타입은 텍스트 본문 없음
    }
```

#### 국립민속박물관 (설화/이야기 · 이미지)

- API: 공공데이터포털 `data.go.kr` 경유
- 응답 파싱: 소장품명, 설명, 이미지URL, 설화 본문
- **미디어 타입**: `image` 또는 `text`

```python
async def fetch_folk_museum(keyword: str) -> dict | None:
    """국립민속박물관 소장품/설화"""
    if not settings.folk_museum_api_key:
        return None
    # 소장품 API (이미지)
    url_collection = "https://api.data.go.kr/openapi/tn_pubr_public_nfm_collection_api"
    params = {
        "serviceKey": settings.folk_museum_api_key,
        "pageNo": 1, "numOfRows": 10, "type": "json",
        "searchNm": keyword,
    }
    # 설화/이야기 API (텍스트) — 실제 API 확인 필요
    # ...
    
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url_collection, params=params)
        resp.raise_for_status()
    items = resp.json().get("response", {}).get("body", {}).get("items", [])
    if not items:
        return None
    item = random.choice(items[:5]) if isinstance(items, list) else items
    return {
        "title": item.get("colctnNm", ""),
        "description": item.get("colctnExplcn", ""),
        "media_url": item.get("imageUrl"),
        "media_type": "image",  # 또는 API 응답에 따라 "text"로 분기
        "source": "국립민속박물관",
        "source_url": "https://www.nfm.go.kr",
        "text_content": item.get("storyText") or None,  # 설화 본문이 있으면 저장
    }
```

#### 국립국악원 (음원)

- API: 공공데이터포털 `국립국악원_음원서비스` API
- 응답: 음원 스트리밍 URL 또는 MP3 다운로드 링크, 음원 길이
- **미디어 타입**: `audio`

```python
async def fetch_gugak(keyword: str) -> dict | None:
    """국립국악원 음원"""
    if not settings.gugak_api_key:
        return None
    url = "https://api.data.go.kr/openapi/tn_pubr_public_gugak_service_api"
    params = {
        "serviceKey": settings.gugak_api_key,
        "pageNo": 1, "numOfRows": 10, "type": "json",
        "musicNm": keyword,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
    items = resp.json().get("response", {}).get("body", {}).get("items", [])
    if not items:
        return None
    item = random.choice(items[:5]) if isinstance(items, list) else items
    return {
        "title": item.get("musicNm", ""),
        "description": item.get("musicDc", ""),
        "media_url": item.get("musicFileUrl"),
        "media_type": "audio",
        "source": "국립국악원",
        "source_url": "https://www.gugak.go.kr",
        "duration_seconds": item.get("playTime"),  # 음원 길이(초)
        "text_content": None,
    }
```

---

## 6. Step 3 — 미디어(비정형 데이터) 파싱 · 캐싱 · 서빙

### 6-1. 미디어 유효성 검증

```python
async def validate_media_url(url: str | None) -> str | None:
    """URL HEAD 요청으로 접근 가능 여부 확인"""
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.head(url, follow_redirects=True)
            return url if resp.status_code == 200 else None
    except Exception:
        return None
```

### 6-2. 미디어 캐싱 (로컬 파일시스템)

```python
import hashlib, os

async def cache_media(url: str, media_type: str) -> str:
    """미디어 파일을 로컬에 캐시하고 서빙 가능한 경로 반환"""
    cache_dir = settings.media_cache_dir
    os.makedirs(cache_dir, exist_ok=True)
    
    # 확장자 결정
    ext_map = {"image": "jpg", "audio": "mp3", "video": "mp4", "text": "txt"}
    ext = ext_map.get(media_type, "bin")
    
    filename = hashlib.md5(url.encode()).hexdigest() + f".{ext}"
    local_path = os.path.join(cache_dir, filename)
    
    if not os.path.exists(local_path):
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
        async with aiofiles.open(local_path, "wb") as f:
            await f.write(resp.content)
    
    # 백엔드 서빙 URL (main.py에 StaticFiles 마운트 필요)
    return f"/media/{filename}"
```

### 6-3. StaticFiles 서빙 마운트

**파일**: `backend/app/main.py`

```python
from fastapi.staticfiles import StaticFiles

app.mount("/media", StaticFiles(directory=settings.media_cache_dir), name="media")
```

### 6-4. 미디어 타입별 사용자 경험

| 미디어 타입 | 노인용 (`ElderlyMain.tsx`) | 청년용 (`YouthMain.tsx`) |
|---|---|---|
| **image** | 사진 전체 화면 표시 → AI가 TTS로 설명 낭독 → 음성 대화 시작 | 사진 + 텍스트 제시 → 텍스트 입력 유도 |
| **audio** | 큰 재생 버튼 → 음원 재생 → "이 소리 기억나세요?" 음성 유도 | 음악 재생 버튼 → "이 소리가 떠올리는 기억을 써주세요" |
| **video** | 짧은 클립(30초 이내) 재생 → 음성 대화 유도 | 영상 + 텍스트 → 텍스트 입력 |
| **text** | AI가 TTS로 설화/이야기 낭독 → "이런 이야기 들어보신 적 있으세요?" | 텍스트 본문 스크롤뷰 → "이 이야기가 떠올리는 걸 써주세요" |

---

## 7. Step 4 — 복지사 듀얼 협의 시스템

### 7-1. 상세 협의 (자연어 대화)

**파일**: `backend/app/routers/welfare.py` 또는 별도 `admin.py`

복지사가 자유 텍스트로 의도를 표현 → AI가 질문을 던져 구체화 → 공공데이터 검색 → 후보 제안 + 근거 → 복지사 피드백 → 최종 선택

```python
async def consult_topic_detailed(welfare_input: str, welfare_id: str) -> dict:
    """복지사 상세 협의: 자연어 대화 기반 주제 구성"""
    # 1. 복지사 의도 파싱 (Claude API)
    parse_prompt = f"""
    복지사의 의도를 분석하여 다음을 추출하세요:
    - 원하는 카테고리 (먹거리/공간/사람/소리/사건)
    - 원하는 감정 톤 (밝은/그리운/평온한/생동감)
    - 미디어 타입 선호 (사진/음악/설화/영상)
    - 특정 지역 언급 여부
    
    복지사 입력: {welfare_input}
    """
    parsed = await generate_text(parse_prompt, max_tokens=200)
    
    # 2. 공공데이터 검색 (상위 3개 후보)
    candidates = await search_public_data(parsed)
    
    # 3. AI가 후보 설명 + 미리보기 정보 구성
    enriched = []
    for c in candidates:
        enriched.append({
            "id": c["id"],
            "title": c["title"],
            "media_type": c["media_type"],
            "preview_url": c["media_url"],  # 실제 URL (미리보기용)
            "source": c["source"],
            "ai_suggested_question": await generate_topic_question(c["title"], c.get("description", "")),
        })
    
    return {
        "welfare_input": welfare_input,
        "parsed_intent": parsed,
        "candidates": enriched,
        "next_action": "복지사가 후보 중 1개를 선택하거나, 피드백을 주세요",
    }
```

### 7-2. 간단 협의 (폼/위저드)

**파일**: `backend/app/routers/welfare.py`

```python
async def consult_topic_simple(
    category: str,      # 'food' | 'space' | 'people' | 'sound' | 'event'
    mood: str,          # 'bright' | 'nostalgic' | 'calm' | 'lively'
    media_pref: str,    # 'image' | 'audio' | 'text' | 'any'
    welfare_id: str,
) -> dict:
    """복지사 간단 협의: 3단계 폼 기반 주제 선택"""
    
    # 1. 키워드 풀에서 카테고리 기반 키워드 선택
    keyword_map = {
        'food': ["전통 시장", "명절 음식", "간식", "농사"],
        'space': ["동네", "학교", "고향", "골목"],
        'people': ["가족", "이웃", "스승", "친구"],
        'sound': ["민요", "학교 종", "장단", "방송"],
        'event': ["첫 월급", "결혼", "이사", "명절"],
    }
    keywords = keyword_map.get(category, ["한국"])
    keyword = random.choice(keywords)
    
    # 2. 미디어 타입 선호 반영하여 API 선택
    fetchers = []
    if media_pref in ('image', 'any') and settings.archives_api_key:
        fetchers.append(fetch_archives)
    if media_pref in ('audio', 'any') and settings.gugak_api_key:
        fetchers.append(fetch_gugak)
    if media_pref in ('text', 'any', 'image') and settings.folk_museum_api_key:
        fetchers.append(fetch_folk_museum)
    
    # 3. 후보 3개 수집
    candidates = []
    random.shuffle(fetchers)
    for fetcher in fetchers:
        if len(candidates) >= 3:
            break
        try:
            result = await fetcher(keyword)
            if result:
                candidates.append(result)
        except Exception:
            continue
    
    # 4. AI가 각 후보에 대해 질문 생성
    for c in candidates:
        c["ai_suggested_question"] = await generate_topic_question(
            c["title"], c.get("description", "")
        )
    
    return {
        "category": category,
        "mood": mood,
        "keyword_used": keyword,
        "candidates": candidates,
    }
```

### 7-3. 질문 유형 선택

복지사가 후보 중 1개를 선택한 후, **질문 유형을 직접 선택**:

| 유형 | 코드 | 노인용 예시 | 청년용 예시 |
|---|---|---|---|
| **선택형** | `choice` | "이 시장에서 어떤 것을 사셨나요? ① 채소 ② 고기 ③ 옷감 ④ 기타" | "이 노래를 들어본 적 있나요? ① 네 ② 아니오 ③ 잘 모르겠어요" |
| **서술형** | `narrative` | "그 시장에서 가장 기억에 남는 장면을 이야기해 주세요" | "이 소리가 떠올리는 기억을 자유롭게 써주세요" |
| **혼합형** | `mixed` | "가족과 함께 가셨나요? 예/아니오 → 어떤 기분이었나요?" | "어릴 때 들어본 적 있나요? ① 네 ② 아니오 → 어떤 장면이 떠오르나요?" |

```python
# 복지사가 최종 선택 + 질문 유형 선택 후 저장
async def publish_topic(
    welfare_id: str,
    selected_candidate: dict,
    question_type: str,  # 'choice' | 'narrative' | 'mixed'
    custom_question: str | None = None,  # 복지사가 AI 질문을 수정한 경우
) -> WeeklyTopic:
    """복지사가 최종 주제를 발행"""
    
    # 1. 미디어 캐싱 (media_url이 있으면)
    if selected_candidate.get("media_url"):
        cached_url = await cache_media(
            selected_candidate["media_url"],
            selected_candidate.get("media_type", "image")
        )
        selected_candidate["media_url"] = cached_url
    
    # 2. 질문 확정 (복지사 수정 우선)
    final_question = custom_question or selected_candidate.get("ai_suggested_question", "")
    
    # 3. DB 저장
    welfare = await get_welfare_worker(welfare_id)
    topic_data = {
        "title": selected_candidate["title"],
        "description": selected_candidate.get("description", ""),
        "media_url": selected_candidate.get("media_url"),
        "media_type": selected_candidate.get("media_type", "text"),
        "source": selected_candidate.get("source", ""),
        "source_url": selected_candidate.get("source_url", ""),
        "ai_question": final_question,
        "text_content": selected_candidate.get("text_content"),
        "duration_seconds": selected_candidate.get("duration_seconds"),
        "region": welfare.region,
        "welfare_id": welfare.id,
        "question_type": question_type,
        "is_customized": True,
    }
    
    async with AsyncSessionLocal() as db:
        topic = await save_weekly_topic(db, topic_data)
    return topic
```

---

## 8. Step 5 — 지역 기반 주제 배분

### 8-1. get_active_topic() 수정

**파일**: `backend/app/services/public_data.py`

```python
async def get_active_topic(
    db: AsyncSession,
    region: str = "default",   # 사용자의 지역
) -> dict:
    """이번 주 활성 주제: DB 우선 (지역 기준), 없으면 TOPIC_POOL 폴백"""
    from datetime import date, timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    # 1. 해당 지역의 주제 우선 조회
    result = await db.execute(
        select(WeeklyTopic)
        .where(
            WeeklyTopic.active_week == monday,
            WeeklyTopic.region == region,
        )
        .order_by(WeeklyTopic.is_customized.desc())  # 지역 특화 우선
    )
    topic = result.scalar_one_or_none()
    
    # 2. 해당 지역에 없으면 중앙 기본 주제("") 조회
    if not topic:
        result = await db.execute(
            select(WeeklyTopic)
            .where(
                WeeklyTopic.active_week == monday,
                WeeklyTopic.region == "default",
            )
        )
        topic = result.scalar_one_or_none()
    
    # 3. DB에 있으면 반환
    if topic:
        return {
            "id": str(topic.id),
            "title": topic.title,
            "description": topic.description,
            "media_url": topic.media_url,
            "media_type": topic.media_type,
            "source": topic.source,
            "source_url": topic.source_url,
            "ai_question": topic.ai_question,
            "text_content": topic.text_content,
            "question_type": topic.question_type,
            "active_week": topic.active_week.isoformat(),
        }
    
    # 4. 폴백: 하드코딩 풀
    idx = monday.isocalendar().week % len(TOPIC_POOL)
    topic = TOPIC_POOL[idx].copy()
    topic["id"] = None
    topic["active_week"] = monday.isoformat()
    topic["media_url"] = None
    topic["question_type"] = "narrative"
    return topic
```

### 8-2. 사용자 앱에서 지역 전달

**파일**: `backend/app/routers/chat.py`

```python
# 사용자 등록 시 지역(region) 필드 추가 필요
# 또는 welfare_id를 통해 지역을 조회

@router.get("/topic", summary="이번 주 주제 조회 (지역 기반)")
async def get_topic(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    # 사용자의 welfare_id → region 조회
    result = await db.execute(
        select(User.welfare_id).where(User.id == uuid.UUID(user_id))
    )
    welfare_id = result.scalar_one_or_none()
    
    region = "default"
    if welfare_id:
        w_result = await db.execute(
            select(WelfareWorker.region).where(WelfareWorker.id == welfare_id)
        )
        region = w_result.scalar_one_or_none() or "default"
    
    topic = await public_data.get_active_topic(db, region=region)
    return topic
```

---

## 9. Step 6 — APScheduler 자동 발행 + 미발행 Fallback

### 9-1. 의존성

`requirements.txt`에 이미 `apscheduler==3.10.4` 존재. `aiofiles` 추가 필요:

```
aiofiles==23.2.1
```

### 9-2. Scheduler 설정

**파일**: `backend/app/main.py`

기존 `lifespan` 기반 구조를 유지하며 scheduler를 통합:

```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger("ium.scheduler")
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # KoBERT 모델 백그라운드 로드
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, preload_emotion)
    
    # APScheduler 시작
    scheduler.add_job(
        publish_weekly_default_topic,
        CronTrigger(day_of_week="mon", hour=0, minute=0),
        id="weekly_topic_publish",
        replace_existing=True,
    )
    scheduler.add_job(
        remind_pending_welfare_workers,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_reminder",
        replace_existing=True,
    )
    scheduler.add_job(
        emergency_publish_by_admin,
        CronTrigger(day_of_week="wed", hour=0, minute=0),
        id="emergency_publish",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[Scheduler] 주간 주제 발행/리마인더/임시발행 스케줄러 시작")
    
    yield
    
    scheduler.shutdown()
    logger.info("[Scheduler] 스케줄러 종료")
```

### 9-3. 자동 발행 함수

```python
async def publish_weekly_default_topic():
    """매주 월요일 00:00 — 중앙 기본 주제 자동 생성"""
    keyword = random.choice(KEYWORD_POOL)
    
    fetchers = []
    if settings.archives_api_key: fetchers.append(fetch_archives)
    if settings.folk_museum_api_key: fetchers.append(fetch_folk_museum)
    if settings.gugak_api_key: fetchers.append(fetch_gugak)
    
    topic_data = None
    random.shuffle(fetchers)
    for fetcher in fetchers:
        try:
            topic_data = await fetcher(keyword)
            if topic_data:
                break
        except Exception as e:
            logger.error(f"[PublicData] {fetcher.__name__} 실패: {e}")
    
    if topic_data is None:
        logger.warning("[PublicData] 모든 API 실패, TOPIC_POOL에서 기본 주제 선택")
        topic_data = TOPIC_POOL[datetime.now().isocalendar().week % len(TOPIC_POOL)].copy()
    
    # 미디어 캐싱
    if topic_data.get("media_url"):
        validated = await validate_media_url(topic_data["media_url"])
        if validated:
            topic_data["media_url"] = await cache_media(validated, topic_data.get("media_type", "image"))
    
    # AI 질문 생성
    topic_data["ai_question"] = await generate_topic_question(
        topic_data["title"], topic_data.get("description", "")
    )
    
    # DB 저장 (region='default', welfare_id=None, is_customized=False)
    topic_data["region"] = "default"
    topic_data["welfare_id"] = None
    topic_data["is_customized"] = False
    topic_data["question_type"] = "narrative"  # 기본값
    
    async with AsyncSessionLocal() as db:
        await save_weekly_topic(db, topic_data)
    
    logger.info(f"[Scheduler] 중앙 기본 주제 발행 완료: {topic_data['title']}")


async def remind_pending_welfare_workers():
    """월요일 09:00 — 아직 지역 특화 주제를 발행하지 않은 복지사에게 리마인더"""
    async with AsyncSessionLocal() as db:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        
        # 이번 주에 지역 주제를 발행한 복지사 목록
        published = await db.execute(
            select(WeeklyTopic.welfare_id)
            .where(
                WeeklyTopic.active_week == monday,
                WeeklyTopic.is_customized == True,
            )
            .distinct()
        )
        published_welfare_ids = {row[0] for row in published.all()}
        
        # 전체 복지사 중 미발행자
        all_welfare = await db.execute(select(WelfareWorker))
        for w in all_welfare.scalars().all():
            if w.id not in published_welfare_ids:
                # 리마인더 발송 (Push / 이메일 / 대시보드 배너 — Phase 2 구체화)
                logger.warning(f"[Reminder] 복지사 {w.name}({w.region}) 미발행 — 리마인더 필요")
                # TODO: 실제 알림 전송 (Push, 이메일, SMS)


async def emergency_publish_by_admin():
    """수요일 00:00 — 미발행 복지사 지역에 중앙 관리자가 임시 발행"""
    async with AsyncSessionLocal() as db:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        
        # 미발행 복지사 목록
        published = await db.execute(
            select(WeeklyTopic.welfare_id)
            .where(
                WeeklyTopic.active_week == monday,
                WeeklyTopic.is_customized == True,
            )
            .distinct()
        )
        published_welfare_ids = {row[0] for row in published.all()}
        
        all_welfare = await db.execute(select(WelfareWorker))
        for w in all_welfare.scalars().all():
            if w.id not in published_welfare_ids:
                # 중앙 기본 주제를 해당 지역에 복제 (is_customized=False로 저장)
                base_topic = await db.execute(
                    select(WeeklyTopic)
                    .where(
                        WeeklyTopic.active_week == monday,
                        WeeklyTopic.region == "default",
                    )
                )
                base = base_topic.scalar_one_or_none()
                if base:
                    emergency_topic = WeeklyTopic(
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
                        welfare_id=None,  # 중앙 관리자 임시 발행
                        question_type=base.question_type,
                        is_customized=False,  # 중앙 주제 그대로임을 표시
                        parent_topic_id=base.id,
                    )
                    db.add(emergency_topic)
                    logger.warning(f"[Emergency] {w.region} 지역 임시 발행: {base.title}")
        
        await db.commit()
```

---

## 10. API 엔드포인트 요약

| 메서드 | 엔드포인트 | 설명 | 권한 |
|---|---|---|---|
| `GET` | `/welfare/topics/default` | 이번 주 중앙 기본 주제 조회 | 복지사 |
| `POST` | `/welfare/topics/consult` | 상세 협의 (자연어) 시작 | 복지사 |
| `POST` | `/welfare/topics/simple-consult` | 간단 협의 (폼) 후보 생성 | 복지사 |
| `POST` | `/welfare/topics/publish` | 복지사가 최종 주제 발행 | 복지사 |
| `GET` | `/welfare/topics/pending` | 복지사 본인의 미발행 여부 확인 | 복지사 |
| `POST` | `/admin/topics/remind` | 미발행 복지사 리마인더 수동 발송 | 중앙 관리자 |
| `POST` | `/admin/topics/emergency-publish` | 상위 기관 임시 발행 수동 트리거 | 중앙 관리자 |
| `POST` | `/admin/topics/publish` | 중앙 기본 주제 수동 발행 (관리자) | 중앙 관리자 |
| `GET` | `/chat/topic` | 사용자가 이번 주 주제 조회 (지역 기반) | 사용자 |

---

## 11. 변경 파일 요약

| 파일 | 변경 내용 |
|---|---|
| `backend/app/config.py` | `archives_api_key`, `folk_museum_api_key`, `gugak_api_key`, `media_cache_dir` 추가 |
| `backend/app/services/public_data.py` | 전면 재작성 — 3개 API 클라이언트, 미디어 캐싱, AI 질문 생성, DB 저장, 지역 기반 조회 |
| `backend/app/routers/chat.py` | `get_active_topic(db, region)` — region 인수 전달 |
| `backend/app/routers/welfare.py` | 주제 발행/협의/조회 API 추가 |
| `backend/app/main.py` | APScheduler(3개 job) + StaticFiles 마운트 |
| `backend/init.sql` | `weekly_topics` 컬럼 추가, `topic_proposals` 테이블 신규 |
| `backend/requirements.txt` | `aiofiles` 추가 |
| `.env.example` | 3개 API 키 항목 추가 |

---

## 12. 테스트 시나리오

1. **API 키 없을 때**: TOPIC_POOL 폴백 정상 동작 확인
2. **API 키 있을 때**: `POST /admin/topics/publish` 호출 → DB에 저장 확인
3. **미디어 URL**: `GET /chat/topic` 응답에 `media_url` 값 존재 확인
4. **캐시 재사용**: 동일 URL 두 번 호출 시 파일 재다운로드 없음 확인
5. **AI 질문**: 생성된 `ai_question`이 한국어 열린 질문 형태인지 확인
6. **지역 필터링**: 종로구 사용자가 종로구 주제를 받는지 확인
7. **질문 유형**: `question_type='choice'`일 때 선택형 UI 노출 확인
8. **미발행 Fallback**: 복지사 미발행 → 수요일에 중앙 주제가 해당 지역에 복제되는지 확인
9. **리마인더**: 월요일 09:00에 미발행 복지사에게 알림 로그 확인
10. **상세 협의**: 복지사가 자연어로 "이번 주 밝은 추억으로 3개 추천해줘" 입력 → 후보 3개 반환 확인

---

## 13. 다음 파이프라인

> **B — 사용자 대화**: `topic_id` 연결, `localhost:8000` 하드코딩 수정, 질문 유형별 UI 분기
> **C — 주제별 감정 집계**: `emotion.py`에 지역/주제 기반 집계 추가
> **D — 수필 생성**: `essay.py` router의 `topic_id` 필터링 버그 수정

---

*작성일: 2026년 6월 1일*
*기준: 이음(以音) 상세계획서 + 사용자-개발자 협의 내용 반영*
