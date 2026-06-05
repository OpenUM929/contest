# Pipeline A — 공공데이터 수집 · 주제 선정 상세 구현 계획

> **의존**: 없음 (최우선 파이프라인)  
> **영향**: B(주제 전달), D(수필 주제), C(주제별 감정 집계)  
> **작성 기준일**: 2026년 6월 1일

---

## 현재 코드 상태 (진단)

| 파일 | 현재 상태 | 문제 |
|---|---|---|
| `backend/app/services/public_data.py` | `TOPIC_POOL` 5개 하드코딩 | 공공 API 0% 연동 |
| `public_data.py:51-60` | `get_active_topic()` — DB 미조회, 산술 인덱싱 | 새 주제 추가 불가 |
| `public_data.py:63-79` | `fetch_from_archives_api()` — 정의만 존재, 호출 없음 | 실 데이터 수집 불가 |
| `models/models.py:37-51` | `WeeklyTopic` 테이블 스키마 완성 | DB 구조는 준비됨 |
| `backend/app/main.py` | APScheduler 없음 | 자동 발행 불가 |

---

## 구현 목표 (단계별)

```
[Step 1] 공공 API 클라이언트 구현
         국가기록원 / 국립민속박물관 / 국립국악원 각 API 호출 함수

[Step 2] 미디어 파싱 및 캐싱
         image URL 검증 / audio 파일 다운로드 / story 텍스트 정제

[Step 3] AI 주제 질문 자동 생성
         Claude API → 연령대별 대화 유도 질문 2개 생성

[Step 4] weekly_topics DB 저장
         get_active_topic() → DB 조회 우선으로 전환

[Step 5] APScheduler 매주 월요일 자동 발행
         main.py에 scheduler 추가
```

---

## Step 1 — 공공 API 클라이언트

### 1-1. 환경변수 추가

**파일**: `backend/app/config.py`

현재 `public_data_api_key` 단일 키만 존재. 3개 기관 키로 분리:

```python
# 추가할 환경변수
ARCHIVES_API_KEY: str = ""          # 국가기록원
FOLK_MUSEUM_API_KEY: str = ""       # 국립민속박물관
GUGAK_API_KEY: str = ""             # 국립국악원
MEDIA_CACHE_DIR: str = "/tmp/ium_media"  # 미디어 캐시 경로
```

**파일**: `.env.example` — 세 개 키 항목 추가

### 1-2. API 클라이언트 구현

**파일**: `backend/app/services/public_data.py` — 전면 재작성

#### 국가기록원 (이미지/문서)
- API: `https://www.archives.go.kr/next/api/searchRecords.do`
- 파라미터: `systemId`, `keyword`, `pageSize=10`, `pageNum=1`
- 응답 파싱: `result.list[].thumbnailUrl`, `result.list[].title`
- 검색 키워드 풀: `["1960년대 서울", "1970년대 농촌", "전통 시장", "고향 마을", "명절 풍경"]`

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
        "media_url": item.get("thumbnailUrl"),
        "media_type": "image",
        "source": "국가기록원",
        "source_url": f"https://www.archives.go.kr/next/content/listSubjectDescription.do?id={item.get('id','')}",
    }
```

#### 국립민속박물관 (설화/이야기)
- API: `https://www.nfm.go.kr/openapi/openapi.do` (공공데이터포털 경유)
- 대안: 공공데이터포털 `data.go.kr` — 국립민속박물관 소장품 API
- 응답 파싱: `item.imageUrl`, `item.name`, `item.content`

```python
async def fetch_folk_museum(keyword: str) -> dict | None:
    """국립민속박물관 소장품/설화"""
    if not settings.folk_museum_api_key:
        return None
    url = "https://api.data.go.kr/openapi/tn_pubr_public_nfm_collection_api"
    params = {
        "serviceKey": settings.folk_museum_api_key,
        "pageNo": 1,
        "numOfRows": 10,
        "type": "json",
        "searchNm": keyword,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
    items = resp.json().get("response", {}).get("body", {}).get("items", [])
    if not items:
        return None
    item = random.choice(items[:5]) if isinstance(items, list) else items
    return {
        "title": item.get("colctnNm", ""),
        "description": item.get("colctnExplcn", ""),
        "media_url": item.get("imageUrl"),
        "media_type": "image",
        "source": "국립민속박물관",
        "source_url": "https://www.nfm.go.kr",
    }
```

#### 국립국악원 (음원)
- API: `https://www.gugak.go.kr/site/main/file/fileDownload` (음원 목록)
- 대안: 공공데이터포털 `국립국악원_음원서비스` API
- 응답: 음원 스트리밍 URL 또는 MP3 다운로드 링크

```python
async def fetch_gugak(keyword: str) -> dict | None:
    """국립국악원 음원"""
    if not settings.gugak_api_key:
        return None
    url = "https://api.data.go.kr/openapi/tn_pubr_public_gugak_service_api"
    params = {
        "serviceKey": settings.gugak_api_key,
        "pageNo": 1,
        "numOfRows": 10,
        "type": "json",
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
    }
```

---

## Step 2 — 미디어 파싱 및 캐싱

### 2-1. 미디어 유효성 검증

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

### 2-2. 이미지 캐싱 (로컬 또는 S3)

Phase 1: 로컬 파일시스템 캐시  
Phase 2: S3 업로드 후 CDN URL 반환

```python
import hashlib, aiofiles, os

async def cache_media(url: str, media_type: str) -> str:
    """미디어 파일을 로컬에 캐시하고 서빙 가능한 경로 반환"""
    cache_dir = settings.media_cache_dir
    os.makedirs(cache_dir, exist_ok=True)
    
    ext = "mp3" if media_type == "audio" else "jpg"
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

**파일**: `backend/app/main.py` — StaticFiles 추가:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/media", StaticFiles(directory=settings.media_cache_dir), name="media")
```

---

## Step 3 — AI 주제 질문 자동 생성

**파일**: `backend/app/services/public_data.py`

```python
async def generate_topic_question(title: str, description: str) -> str:
    """Claude API로 연령대별 대화 유도 질문 생성"""
    prompt = f"""다음 문화 자료에 대해 어르신(60~80대)이 자신의 기억과 경험을 떠올리며 이야기할 수 있는
따뜻한 대화 질문을 1문장으로 만들어주세요. 질문은 열린 질문이어야 하며, 
과거 기억을 자연스럽게 끌어낼 수 있어야 합니다.

자료 제목: {title}
자료 설명: {description}

질문만 출력하세요. 다른 설명은 불필요합니다."""
    
    from app.services.claude import generate_text
    question = await generate_text(prompt, max_tokens=100)
    return question.strip()
```

---

## Step 4 — weekly_topics DB 저장 및 get_active_topic 전환

### 4-1. DB 저장 함수

```python
async def save_weekly_topic(db: AsyncSession, topic_data: dict) -> WeeklyTopic:
    """새 주제를 weekly_topics 테이블에 저장"""
    from datetime import date, timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    # 이번 주 주제가 이미 있으면 업데이트
    existing = await db.execute(
        select(WeeklyTopic).where(WeeklyTopic.active_week == monday)
    )
    topic = existing.scalar_one_or_none()
    
    if topic is None:
        topic = WeeklyTopic(active_week=monday)
        db.add(topic)
    
    topic.title = topic_data["title"]
    topic.description = topic_data.get("description", "")
    topic.media_url = topic_data.get("media_url")
    topic.media_type = topic_data.get("media_type")
    topic.source = topic_data.get("source")
    topic.source_url = topic_data.get("source_url")
    topic.ai_question = topic_data.get("ai_question")
    
    await db.commit()
    await db.refresh(topic)
    return topic
```

### 4-2. get_active_topic() — DB 우선 조회로 전환

```python
async def get_active_topic(db: AsyncSession | None = None) -> dict:
    """이번 주 활성 주제: DB 우선, 없으면 TOPIC_POOL 폴백"""
    from datetime import date, timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    if db is not None:
        result = await db.execute(
            select(WeeklyTopic).where(WeeklyTopic.active_week == monday)
        )
        topic = result.scalar_one_or_none()
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
                "active_week": topic.active_week.isoformat(),
            }
    
    # 폴백: 하드코딩 풀
    idx = monday.isocalendar().week % len(TOPIC_POOL)
    topic = TOPIC_POOL[idx].copy()
    topic["id"] = None
    topic["active_week"] = monday.isoformat()
    topic["media_url"] = None
    return topic
```

**chat.py 수정**: `get_active_topic()` 호출 시 `db` 인수 전달:
```python
topic = await public_data.get_active_topic(db)
```

---

## Step 5 — APScheduler 매주 월요일 자동 발행

**파일**: `backend/app/main.py`

### 5-1. 의존성 추가

`requirements.txt`:
```
apscheduler==3.10.4
aiofiles==23.2.1
```

### 5-2. Scheduler 설정

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import AsyncSessionLocal

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

async def publish_weekly_topic():
    """매주 월요일 00:00 — 새 주제 수집 및 발행"""
    import random
    from app.services.public_data import (
        fetch_archives, fetch_folk_museum, fetch_gugak,
        validate_media_url, cache_media, generate_topic_question,
        save_weekly_topic, KEYWORD_POOL
    )
    
    keyword = random.choice(KEYWORD_POOL)
    
    # 3개 소스 중 랜덤 선택 (API 키 있는 것 우선)
    fetchers = []
    if settings.archives_api_key:
        fetchers.append(("archives", fetch_archives))
    if settings.folk_museum_api_key:
        fetchers.append(("folk", fetch_folk_museum))
    if settings.gugak_api_key:
        fetchers.append(("gugak", fetch_gugak))
    
    topic_data = None
    random.shuffle(fetchers)
    for name, fetcher in fetchers:
        try:
            topic_data = await fetcher(keyword)
            if topic_data:
                break
        except Exception as e:
            logger.error(f"[PublicData] {name} fetch 실패: {e}")
    
    if topic_data is None:
        logger.warning("[PublicData] 모든 API 실패, 이번 주 주제 발행 스킵")
        return
    
    # 미디어 캐싱
    if topic_data.get("media_url"):
        validated = await validate_media_url(topic_data["media_url"])
        if validated:
            topic_data["media_url"] = await cache_media(
                validated, topic_data.get("media_type", "image")
            )
    
    # AI 질문 생성
    topic_data["ai_question"] = await generate_topic_question(
        topic_data["title"],
        topic_data.get("description", "")
    )
    
    async with AsyncSessionLocal() as db:
        await save_weekly_topic(db, topic_data)
    
    logger.info(f"[PublicData] 주간 주제 발행 완료: {topic_data['title']}")


@app.on_event("startup")
async def startup_event():
    scheduler.add_job(
        publish_weekly_topic,
        CronTrigger(day_of_week="mon", hour=0, minute=0),
    )
    scheduler.start()
    logger.info("[Scheduler] 주간 주제 발행 스케줄러 시작")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
```

### 5-3. 수동 트리거 API (관리자용)

`main.py` 또는 별도 admin router:

```python
@app.post("/admin/topics/publish", summary="주제 수동 발행 (관리자)")
async def admin_publish_topic():
    await publish_weekly_topic()
    return {"status": "published"}
```

---

## Step 6 — 키워드 풀 관리

```python
KEYWORD_POOL = [
    # 시대별 생활사
    "1950년대 한국", "1960년대 서울", "1970년대 농촌", "1980년대 도시",
    # 전통 문화
    "전통 시장", "명절 풍경", "민요", "설화",
    # 자연 / 계절
    "봄 풍경", "추수", "눈 내리는 마을",
    # 일상
    "골목길", "학교", "가족 사진", "동네 우물",
]
```

---

## API 키 신청 가이드

| 기관 | 신청 URL | 키 발급 소요 | 비고 |
|---|---|---|---|
| 국가기록원 | https://www.archives.go.kr/next/openapi/main.do | 1~3일 | 무료 |
| 국립민속박물관 | https://data.go.kr → "국립민속박물관 소장품" 검색 | 즉시~1일 | 공공데이터포털 경유 |
| 국립국악원 | https://data.go.kr → "국립국악원" 검색 | 즉시~1일 | 공공데이터포털 경유 |

**키 신청 전 임시 조치**: API 키 없을 때 TOPIC_POOL 폴백 유지 (현행 유지)

---

## 변경 파일 요약

| 파일 | 변경 내용 |
|---|---|
| `backend/app/config.py` | `archives_api_key`, `folk_museum_api_key`, `gugak_api_key`, `media_cache_dir` 추가 |
| `backend/app/services/public_data.py` | 전면 재작성 — 3개 API 클라이언트, 미디어 캐시, AI 질문 생성, DB 저장 |
| `backend/app/routers/chat.py` | `get_active_topic(db)` — db 인수 전달 |
| `backend/app/main.py` | APScheduler 추가, StaticFiles 마운트, admin 엔드포인트 |
| `backend/requirements.txt` | `apscheduler`, `aiofiles` 추가 |
| `.env.example` | 3개 API 키 항목 추가 |

---

## 테스트 시나리오

1. **API 키 없을 때**: TOPIC_POOL 폴백 정상 동작 확인
2. **API 키 있을 때**: `POST /admin/topics/publish` 호출 → DB에 저장 확인
3. **미디어 URL**: `GET /chat/topic` 응답에 `media_url` 값 존재 확인
4. **캐시 재사용**: 동일 URL 두 번 호출 시 파일 재다운로드 없음 확인
5. **AI 질문**: 생성된 `ai_question`이 한국어 열린 질문 형태인지 확인

---

> **다음 파이프라인**: B — 사용자 대화 (topic_id 연결, localhost 수정)
