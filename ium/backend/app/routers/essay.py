from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.database import get_db
from app.models.models import Conversation, Essay, WeeklyTopic, EssayContributor
from app.services.essay import generate_essay
from app.services.public_data import get_active_topic

router = APIRouter(prefix="/api/essay", tags=["essay"])


class ArtworkRequest(BaseModel):
    reference_titles: str | None = None


@router.post("/generate", summary="작품 생성 (v3: 장르별 작가 프롬프트, 수량 제한 없음)")
async def create_essay(
    background_tasks: BackgroundTasks,
    topic_id: str | None = Query(None, description="특정 주제 ID (없으면 이번 주 활성 주제 사용)"),
    prompt_version: str = Query("v3", description="프롬프트 버전: v0 | v1 | v2 | v3(장르별 작가)"),
    content_type: str = Query("essay", description="결과물 유형: essay | poem | novel"),
    payload: ArtworkRequest | None = Body(None),
    db: AsyncSession = Depends(get_db),
):
    if topic_id:
        result = await db.execute(select(WeeklyTopic).where(WeeklyTopic.id == uuid.UUID(topic_id)))
        topic_row = result.scalar_one_or_none()
        if not topic_row:
            raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")
        topic_data = {"id": str(topic_row.id), "title": topic_row.title}
    else:
        topic_data = await get_active_topic(db)
        if not topic_data or not topic_data.get("id"):
            raise HTTPException(status_code=404, detail="이번 주 주제가 없습니다.")

    try:
        title, content, contributor_cnt, contributor_stats = await generate_essay(
            topic_id=str(topic_data["id"]),
            topic_title=topic_data["title"],
            db=db,
            prompt_version=prompt_version,
            content_type=content_type,
            reference_titles=payload.reference_titles if payload else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    essay = Essay(
        topic_id=uuid.UUID(topic_data["id"]),
        title=title,
        content=content,
        content_type=content_type,
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
        "content_type": essay.content_type,
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
        "content_type": essay.content_type,
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
            "content_type": e.content_type,
            "contributor_cnt": e.contributor_cnt,
            "published_at": e.published_at.isoformat(),
        }
        for e in essays
    ]


@router.get("/archive", summary="수필 아카이브 (주제별 조회, content_type 필터 지원)")
async def get_essay_archive(
    type: str | None = Query(None, description="content_type 필터 (essay | poem | novel)"),
    db: AsyncSession = Depends(get_db),
):
    """모든 주제별 수필/시/소설 목록을 반환합니다. 이번 주 + 지난 주 모두 포함.
    type 쿼리 파라미터로 결과물 유형 필터링 가능."""
    query = (
        select(Essay, WeeklyTopic)
        .join(WeeklyTopic, Essay.topic_id == WeeklyTopic.id)
        .order_by(Essay.published_at.desc())
    )
    if type:
        query = query.where(Essay.content_type == type)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "essay_id": str(e.id),
            "topic_id": str(t.id) if t else None,
            "topic_title": t.title if t else e.title,
            "active_week": t.active_week.isoformat() if t and t.active_week else None,
            "content_type": e.content_type,
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
        "content_type": essay.content_type,
        "contributor_cnt": essay.contributor_cnt,
        "prompt_version": essay.prompt_version,
        "published_at": essay.published_at.isoformat(),
    }
