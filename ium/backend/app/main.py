import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

print("[main.py] sys.path:", sys.path[:5])

from app.routers import chat, essay, safety, welfare
from app.services.emotion import preload as preload_emotion
from app.config import settings

logger = logging.getLogger("ium.scheduler")
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # StaticFiles 마운트 전 디렉토리 보장
    import os
    os.makedirs(settings.media_cache_dir, exist_ok=True)

    # KoBERT 모델 백그라운드 로드 (로컬 모드에서는 생략 가능)
    if not settings.skip_emotion:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, preload_emotion)
    else:
        logger.info("[Lifespan] 감정 모델 로딩 생략 (로컬 모드)")
    
    # APScheduler 설정 (중앙 기본 주제 자동 발행 + 리마인더 + 임시 발행)
    from app.services.public_data import (
        publish_weekly_default_topic,
        remind_pending_welfare_workers,
        emergency_publish_by_admin,
    )
    
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

    from app.services.alert import daily_safety_check
    scheduler.add_job(
        daily_safety_check,
        CronTrigger(hour=9, minute=0),
        id="daily_safety_check",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("[Scheduler] 주간 주제 발행/리마인더/임시발행/일일안전점검 스케줄러 시작")
    
    yield
    
    scheduler.shutdown()
    logger.info("[Scheduler] 스케줄러 종료")


app = FastAPI(
    title="이음(以音) API",
    description="은둔 청년 + 고독사 위험 노인 연결 AI 사회안전망 플랫폼",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 미디어 파일 서빙 (캐시된 공공데이터 이미지/음원)
app.mount("/media", StaticFiles(directory=settings.media_cache_dir), name="media")

# API 라우터 등록
app.include_router(chat.router)
app.include_router(essay.router)
app.include_router(safety.router)
app.include_router(welfare.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "이음(以音)"}


# 관리자 대시보드는 별도의 Vite dev server (localhost:5173)에서 실행
