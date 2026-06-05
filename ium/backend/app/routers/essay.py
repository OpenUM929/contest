from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.database import get_db
from app.models.models import Conversation, Essay, WeeklyTopic, EssayContributor
from app.services.essay import generate_essay
from app.services.public_data import get_active_topic

router = APIRouter(prefix="/essay", tags=["essay"])


@router.post("/generate", summary="이번 주 수필 생성 (최소 5건 대화 필요)")
async def create_essay(
    background_tasks: BackgroundTasks,
    prompt_version: str = "v0",
    db: AsyncSession = Depends(get_db),
):
    topic = await get_active_topic(db)
    if not topic or not topic.get("id"):
        raise HTTPException(status_code=404, detail="이번 주 주제가 없습니다.")

    title, content, contributor_cnt, contributor_stats = await generate_essay(
        topic_id=str(topic["id"]),
        topic_title=topic["title"],
        db=db,
        prompt_version=prompt_version,
    )

    essay = Essay(
        topic_id=uuid.UUID(topic["id"]),
        title=title,
        content=content,
        contributor_cnt=contributor_cnt,
        prompt_version=prompt_version,
    )
    db.add(essay)
    await db.commit()
    await db.refresh(essay)

    # EssayContributor 기록
    for user_id, msg_count in contributor_stats.items():
        contrib = EssayContributor(
            essay_id=essay.id,
            user_id=uuid.UUID(user_id),
            message_count=msg_count,
        )
        db.add(contrib)
    await db.commit()

    return {
        "essay_id": str(essay.id),
        "title": essay.title,
        "content": essay.content,
        "contributor_cnt": essay.contributor_cnt,
        "prompt_version": essay.prompt_version,
    }


@router.get("/latest", summary="이번 주 수필 조회")
async def get_latest_essay(db: AsyncSession = Depends(get_db)):
    topic = await get_active_topic(db)
    topic_id = topic.get("id") if topic else None

    query = select(Essay).order_by(Essay.published_at.desc()).limit(1)
    if topic_id:
        query = (
            select(Essay)
            .where(Essay.topic_id == uuid.UUID(topic_id))
            .order_by(Essay.published_at.desc())
            .limit(1)
        )

    result = await db.execute(query)
    essay = result.scalar_one_or_none()
    if not essay:
        raise HTTPException(status_code=404, detail="이번 주 수필이 아직 없습니다.")
    return {
        "essay_id": str(essay.id),
        "title": essay.title,
        "content": essay.content,
        "contributor_cnt": essay.contributor_cnt,
        "published_at": essay.published_at.isoformat(),
    }


@router.get("/", summary="수필 목록 조회")
async def list_essays(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Essay).order_by(Essay.published_at.desc()).limit(limit)
    )
    essays = result.scalars().all()
    return [
        {
            "essay_id": str(e.id),
            "title": e.title,
            "contributor_cnt": e.contributor_cnt,
            "published_at": e.published_at.isoformat(),
        }
        for e in essays
    ]


@router.get("/archive", summary="수필 아카이브 (주제별 조회)")
async def get_essay_archive(db: AsyncSession = Depends(get_db)):
    """모든 주제별 수필 목록을 반환합니다. 이번 주 + 지난 주 모두 포함."""
    result = await db.execute(
        select(Essay, WeeklyTopic)
        .join(WeeklyTopic, Essay.topic_id == WeeklyTopic.id)
        .order_by(Essay.published_at.desc())
    )
    rows = result.all()

    return [
        {
            "essay_id": str(e.id),
            "topic_id": str(t.id) if t else None,
            "topic_title": t.title if t else e.title,
            "active_week": t.active_week.isoformat() if t and t.active_week else None,
            "contributor_cnt": e.contributor_cnt,
            "published_at": e.published_at.isoformat(),
        }
        for e, t in rows
    ]


@router.get("/{essay_id}", summary="수필 상세 조회")
async def get_essay_detail(essay_id: str, db: AsyncSession = Depends(get_db)):
    """특정 수필의 전체 내용을 조회합니다."""
    result = await db.execute(
        select(Essay, WeeklyTopic)
        .join(WeeklyTopic, Essay.topic_id == WeeklyTopic.id, isouter=True)
        .where(Essay.id == uuid.UUID(essay_id))
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="수필을 찾을 수 없습니다.")
    essay, topic = row
    return {
        "essay_id": str(essay.id),
        "topic_id": str(topic.id) if topic else None,
        "topic_title": topic.title if topic else essay.title,
        "title": essay.title,
        "content": essay.content,
        "contributor_cnt": essay.contributor_cnt,
        "prompt_version": essay.prompt_version,
        "published_at": essay.published_at.isoformat(),
    }
