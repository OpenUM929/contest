import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

print("[main.py] sys.path:", sys.path[:5])

from app.routers import chat, essay, safety, welfare, auth, admin
from app.services.emotion import preload as preload_emotion
from app.config import settings

logger = logging.getLogger("ium.scheduler")
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # StaticFiles 마운트 전 디렉토리 보장
    os.makedirs(settings.media_cache_dir, exist_ok=True)

    # DB 테이블 생성
    from app.database import create_tables
    await create_tables()
    logger.info("[Lifespan] DB tables checked/created")

    # KoBERT 모델 백그라운드 로드 (로컬 모드에서는 생략 가능)
    if not settings.skip_emotion:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, preload_emotion)
    else:
        logger.info("[Lifespan] emotion model loading skipped")
    
    # APScheduler 설정 (중앙 기본 주제 자동 발행 + 리마인더 + 임시 발행)
    from app.services.public_data import (
        publish_weekly_default_topic,
        remind_pending_welfare_workers,
        emergency_publish_by_admin,
    )
    from app.services.essay import auto_generate_weekly_essay
    
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
    scheduler.add_job(
        auto_generate_weekly_essay,
        CronTrigger(day_of_week="sun", hour=23, minute=0),
        id="weekly_essay_generation",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("[Scheduler] weekly topic/reminder/emergency/safety scheduler started")
    
    yield
    
    scheduler.shutdown()
    logger.info("[Scheduler] scheduler shutdown")


app = FastAPI(
    title="이음(以音) API",
    description="은둔 청년 + 고독사 위험 노인 연결 AI 사회안전망 플랫폼",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Vite 개발 서버 (npm run dev). 기본 5173, 포트 충돌 시 5174 폴백.
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
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
app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "이음(以音)"}


@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    login_path = os.path.join(os.path.dirname(__file__), "static", "login.html")
    if not os.path.exists(login_path):
        return HTMLResponse(content="<h1>login.html not found</h1>", status_code=404)
    with open(login_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/user", response_class=HTMLResponse)
async def user_page():
    user_path = os.path.join(os.path.dirname(__file__), "static", "user.html")
    if not os.path.exists(user_path):
        return HTMLResponse(content="<h1>user.html not found</h1>", status_code=404)
    with open(user_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/sw.js")
async def service_worker_cleanup():
    return Response(
        content="""self.addEventListener('install',function(e){e.skipWaiting()});
self.addEventListener('activate',function(e){e.waitUntil(Promise.all([caches.keys().then(function(n){return Promise.all(n.map(function(c){return caches.delete(c)}))}),self.clients.claim()]))});""",
        media_type="application/javascript",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )


# 관리자 대시보드 정적 파일 서빙 (assets only — SPA fallback handled by /dashboard route)
_dash_dir = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "dist")
_dash_exists = os.path.isdir(_dash_dir)

if _dash_exists:
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_page():
        idx = os.path.join(_dash_dir, "index.html")
        if os.path.isfile(idx):
            with open(idx, "r", encoding="utf-8") as f:
                return f.read()
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)

    app.mount("/", StaticFiles(directory=_dash_dir), name="dashboard")
else:
    logger.warning("[Dashboard] %s not found — dashboard will not be served", _dash_dir)
