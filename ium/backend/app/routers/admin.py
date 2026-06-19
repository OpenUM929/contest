"""관리자 회원/복지사 관리 모듈 (0615_02).

기존 welfare.py / dashboard 는 수정하지 않고 신규로 추가된 모듈입니다.
인증/RBAC 은 본 Phase 범위 밖이며, admin_id 는 "admin" 으로 고정합니다.
(auth.py 의 demo-admin 로그인이 반환하는 user_id="admin" 과 동일한 식별자)
"""
import json
import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import User, WelfareWorker, AdminLog, SafetyAlert

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_ID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"  # seed_accounts.py 고정 UUID (Phase 4에서 JWT/RBAC로 교체)


# ─────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────

def _parse_uuid(value: str, label: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=400, detail=f"잘못된 {label} 형식입니다.")


async def _record_log(
    db: AsyncSession,
    action: str,
    target_type: str,
    target_id: str,
    payload: dict | None = None,
) -> None:
    """관리자 작업 로그를 세션에 추가합니다 (commit 은 호출측에서 수행)."""
    log = AdminLog(
        admin_id=ADMIN_ID,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        payload=json.dumps(payload, ensure_ascii=False) if payload is not None else None,
    )
    db.add(log)


def _serialize_user(u: User, welfare_name: str | None = None) -> dict:
    return {
        "user_id": str(u.id),
        "user_type": u.user_type,
        "name": u.name,
        "nickname": u.nickname,
        "status": u.status,
        "phone": u.phone,
        "email": u.email,
        "region": u.region,
        "welfare_id": str(u.welfare_id) if u.welfare_id else None,
        "welfare_name": welfare_name,
        "note": u.note,
        "last_seen": u.last_seen_at.isoformat() if u.last_seen_at else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
    }


def _serialize_worker(w: WelfareWorker, active_user_cnt: int | None = None) -> dict:
    return {
        "welfare_id": str(w.id),
        "name": w.name,
        "region": w.region,
        "email": w.email,
        "phone": w.phone,
        "role": w.role,
        "status": w.status,
        "note": w.note,
        "active_user_count": active_user_cnt,
        "created_at": w.created_at.isoformat() if w.created_at else None,
        "updated_at": w.updated_at.isoformat() if w.updated_at else None,
    }


async def _assert_nickname_unique(
    db: AsyncSession, nickname: str, exclude_id: uuid.UUID | None = None
) -> None:
    """탈퇴(withdrawn)가 아닌 회원 중 닉네임 중복 여부를 검사합니다 (BR-001)."""
    if not nickname:
        return
    stmt = select(func.count(User.id)).where(
        User.nickname == nickname,
        User.status != "withdrawn",
    )
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    cnt = (await db.execute(stmt)).scalar() or 0
    if cnt > 0:
        raise HTTPException(status_code=409, detail=f"이미 사용 중인 닉네임입니다: {nickname}")


async def _get_active_worker(db: AsyncSession, welfare_id: str) -> WelfareWorker:
    """배정 대상 복지사가 존재하고 active 인지 확인합니다 (BR-004)."""
    w_id = _parse_uuid(welfare_id, "welfare_id")
    result = await db.execute(select(WelfareWorker).where(WelfareWorker.id == w_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="복지사를 찾을 수 없습니다.")
    if worker.status != "active":
        raise HTTPException(status_code=409, detail="비활성 복지사에게는 배정할 수 없습니다.")
    return worker


# ─────────────────────────────────────
# DTO
# ─────────────────────────────────────

class UserCreateRequest(BaseModel):
    user_type: Literal["elder", "youth"]
    name: str
    nickname: str
    phone: Optional[str] = None
    email: Optional[str] = None
    region: Optional[str] = None
    welfare_id: Optional[str] = None
    note: Optional[str] = None


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    region: Optional[str] = None
    welfare_id: Optional[str] = None
    status: Optional[Literal["active", "dormant", "withdrawn"]] = None
    note: Optional[str] = None


class AssignRequest(BaseModel):
    welfare_id: Optional[str] = None   # None 이면 배정 해제


class WorkerCreateRequest(BaseModel):
    name: str
    region: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Literal["admin", "worker"] = "worker"
    note: Optional[str] = None


class WorkerUpdateRequest(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[Literal["admin", "worker"]] = None
    status: Optional[Literal["active", "inactive"]] = None
    note: Optional[str] = None


# ─────────────────────────────────────
# 회원(User) CRUD
# ─────────────────────────────────────

@router.post("/users", summary="회원 등록")
async def create_user(body: UserCreateRequest, db: AsyncSession = Depends(get_db)):
    await _assert_nickname_unique(db, body.nickname)

    welfare_uuid = None
    if body.welfare_id:
        worker = await _get_active_worker(db, body.welfare_id)
        welfare_uuid = worker.id

    user = User(
        user_type=body.user_type,
        name=body.name,
        nickname=body.nickname,
        phone=body.phone,
        email=body.email,
        region=body.region,
        welfare_id=welfare_uuid,
        note=body.note,
        is_anonymous=(body.user_type == "youth"),
        status="active",
    )
    db.add(user)
    await db.flush()  # user.id 확보
    await _record_log(db, "create_user", "user", user.id, {"nickname": body.nickname, "user_type": body.user_type})
    await db.commit()
    await db.refresh(user)
    return _serialize_user(user)


@router.get("/users", summary="회원 목록 (검색+필터+페이징)")
async def list_users(
    q: str = Query("", description="이름/닉네임/연락처 통합 검색"),
    user_type: Optional[str] = None,
    status: Optional[str] = None,
    welfare_id: Optional[str] = None,
    region: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = max(1, min(100, page_size))   # R-006: 최대 100

    conditions = []
    if q.strip():
        kw = f"%{q.strip()}%"
        conditions.append(or_(User.name.ilike(kw), User.nickname.ilike(kw), User.phone.ilike(kw)))
    if user_type:
        conditions.append(User.user_type == user_type)
    if status:
        conditions.append(User.status == status)
    if welfare_id:
        conditions.append(User.welfare_id == _parse_uuid(welfare_id, "welfare_id"))
    if region:
        conditions.append(User.region.ilike(f"%{region}%"))

    base = select(User)
    for c in conditions:
        base = base.where(c)

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0

    result = await db.execute(
        base.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = result.scalars().all()

    # 복지사 이름 매핑
    worker_ids = {u.welfare_id for u in users if u.welfare_id}
    worker_names: dict[uuid.UUID, str] = {}
    if worker_ids:
        w_result = await db.execute(
            select(WelfareWorker.id, WelfareWorker.name).where(WelfareWorker.id.in_(worker_ids))
        )
        worker_names = {row[0]: row[1] for row in w_result.all()}

    return {
        "items": [_serialize_user(u, worker_names.get(u.welfare_id)) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.patch("/users/{user_id}", summary="회원 수정")
async def update_user(user_id: str, body: UserUpdateRequest, db: AsyncSession = Depends(get_db)):
    u_id = _parse_uuid(user_id, "user_id")
    result = await db.execute(select(User).where(User.id == u_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

    data = body.model_dump(exclude_unset=True)
    changes: dict = {}

    if "nickname" in data and data["nickname"] != user.nickname:
        await _assert_nickname_unique(db, data["nickname"], exclude_id=user.id)

    if "welfare_id" in data:
        if data["welfare_id"]:
            worker = await _get_active_worker(db, data["welfare_id"])
            data["welfare_id"] = worker.id
        else:
            data["welfare_id"] = None

    for field, value in data.items():
        old = getattr(user, field)
        new = str(value) if isinstance(value, uuid.UUID) else value
        old_cmp = str(old) if isinstance(old, uuid.UUID) else old
        if old_cmp != new:
            changes[field] = {"before": old_cmp, "after": new}
            setattr(user, field, value)

    if changes:
        await _record_log(db, "update_user", "user", user.id, changes)
    await db.commit()
    await db.refresh(user)
    return _serialize_user(user)


@router.delete("/users/{user_id}", summary="회원 삭제 (소프트)")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    u_id = _parse_uuid(user_id, "user_id")
    result = await db.execute(select(User).where(User.id == u_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
    if user.status == "withdrawn":
        raise HTTPException(status_code=409, detail="이미 탈퇴 처리된 회원입니다.")

    # BR-002: 소프트 삭제
    user.status = "withdrawn"
    user.phone = None
    user.email = None
    if user.nickname and not user.nickname.startswith("[탈퇴]"):
        user.nickname = f"[탈퇴] {user.nickname}"

    await _record_log(db, "delete_user", "user", user.id, {"nickname": user.nickname})
    await db.commit()
    return {"user_id": str(user.id), "status": "withdrawn"}


@router.post("/users/{user_id}/assign", summary="복지사 배정/재배정")
async def assign_worker(user_id: str, body: AssignRequest, db: AsyncSession = Depends(get_db)):
    u_id = _parse_uuid(user_id, "user_id")
    result = await db.execute(select(User).where(User.id == u_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

    old_welfare = str(user.welfare_id) if user.welfare_id else None
    if body.welfare_id:
        worker = await _get_active_worker(db, body.welfare_id)
        user.welfare_id = worker.id
    else:
        user.welfare_id = None

    await _record_log(
        db, "assign_worker", "user", user.id,
        {"before": old_welfare, "after": str(user.welfare_id) if user.welfare_id else None},
    )
    await db.commit()
    await db.refresh(user)
    return _serialize_user(user)


# ─────────────────────────────────────
# 복지사-회원 할당 API (일괄)
# ─────────────────────────────────────


class BulkAssignRequest(BaseModel):
    user_ids: list[str]


@router.get("/workers/{welfare_id}/users", summary="복지사 배정 회원 목록")
async def get_worker_users(
    welfare_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    w_id = _parse_uuid(welfare_id, "welfare_id")
    conditions = [User.welfare_id == w_id]
    base = select(User).where(*conditions)
    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0
    result = await db.execute(
        base.order_by(User.nickname)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = result.scalars().all()
    return {
        "items": [_serialize_user(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/workers/{welfare_id}/assign", summary="복지사에 회원 일괄 배정")
async def bulk_assign_worker(
    welfare_id: str,
    body: BulkAssignRequest,
    db: AsyncSession = Depends(get_db),
):
    w_id = _parse_uuid(welfare_id, "welfare_id")
    worker = await _get_active_worker(db, welfare_id)
    if not worker:
        raise HTTPException(status_code=404, detail="복지사를 찾을 수 없습니다.")

    assigned = []
    for uid in body.user_ids:
        u_id = _parse_uuid(uid, "user_id")
        result = await db.execute(select(User).where(User.id == u_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail=f"회원 ID '{uid}'를 찾을 수 없습니다.")
        old_welfare = str(user.welfare_id) if user.welfare_id else None
        user.welfare_id = worker.id
        assigned.append({"user_id": str(user.id), "old_welfare_id": old_welfare, "new_welfare_id": str(worker.id)})

    await _record_log(
        db, "bulk_assign_worker", "worker", welfare_id,
        {"assigned_count": len(assigned), "user_ids": body.user_ids},
    )
    await db.commit()
    return {"assigned": assigned, "count": len(assigned)}


@router.post("/workers/{welfare_id}/unassign", summary="복지사에서 회원 일괄 해제")
async def bulk_unassign_worker(
    welfare_id: str,
    body: BulkAssignRequest,
    db: AsyncSession = Depends(get_db),
):
    w_id = _parse_uuid(welfare_id, "welfare_id")
    unassigned = []
    for uid in body.user_ids:
        u_id = _parse_uuid(uid, "user_id")
        result = await db.execute(select(User).where(User.id == u_id, User.welfare_id == w_id))
        user = result.scalar_one_or_none()
        if not user:
            continue
        old_welfare = str(user.welfare_id)
        user.welfare_id = None
        unassigned.append({"user_id": str(user.id), "old_welfare_id": old_welfare})

    await _record_log(
        db, "bulk_unassign_worker", "worker", welfare_id,
        {"unassigned_count": len(unassigned), "user_ids": body.user_ids},
    )
    await db.commit()
    return {"unassigned": unassigned, "count": len(unassigned)}


# ─────────────────────────────────────
# 복지사(WelfareWorker) CRUD
# ─────────────────────────────────────

async def _active_user_count(db: AsyncSession, welfare_id: uuid.UUID) -> int:
    cnt = (await db.execute(
        select(func.count(User.id)).where(
            User.welfare_id == welfare_id,
            User.status == "active",
        )
    )).scalar() or 0
    return cnt


@router.post("/workers", summary="복지사 등록")
async def create_worker(body: WorkerCreateRequest, db: AsyncSession = Depends(get_db)):
    worker = WelfareWorker(
        name=body.name,
        region=body.region,
        email=body.email,
        phone=body.phone,
        role=body.role,
        note=body.note,
        status="active",
    )
    db.add(worker)
    await db.flush()
    await _record_log(db, "create_worker", "worker", worker.id, {"name": body.name, "role": body.role})
    await db.commit()
    await db.refresh(worker)
    return _serialize_worker(worker, active_user_cnt=0)


@router.get("/workers", summary="복지사 목록 (검색+필터+페이징)")
async def list_workers(
    q: str = Query("", description="이름/지역 검색"),
    status: Optional[str] = None,
    role: Optional[str] = None,
    region: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    conditions = []
    if q.strip():
        kw = f"%{q.strip()}%"
        conditions.append(or_(WelfareWorker.name.ilike(kw), WelfareWorker.region.ilike(kw)))
    if status:
        conditions.append(WelfareWorker.status == status)
    if role:
        conditions.append(WelfareWorker.role == role)
    if region:
        conditions.append(WelfareWorker.region.ilike(f"%{region}%"))

    base = select(WelfareWorker)
    for c in conditions:
        base = base.where(c)

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0

    result = await db.execute(
        base.order_by(WelfareWorker.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    workers = result.scalars().all()

    items = []
    for w in workers:
        items.append(_serialize_worker(w, await _active_user_count(db, w.id)))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.patch("/workers/{welfare_id}", summary="복지사 수정")
async def update_worker(welfare_id: str, body: WorkerUpdateRequest, db: AsyncSession = Depends(get_db)):
    w_id = _parse_uuid(welfare_id, "welfare_id")
    result = await db.execute(select(WelfareWorker).where(WelfareWorker.id == w_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="복지사를 찾을 수 없습니다.")

    data = body.model_dump(exclude_unset=True)
    changes: dict = {}
    for field, value in data.items():
        old = getattr(worker, field)
        if old != value:
            changes[field] = {"before": old, "after": value}
            setattr(worker, field, value)

    if changes:
        await _record_log(db, "update_worker", "worker", worker.id, changes)
    await db.commit()
    await db.refresh(worker)
    return _serialize_worker(worker, await _active_user_count(db, worker.id))


@router.delete("/workers/{welfare_id}", summary="복지사 삭제 (보호)")
async def delete_worker(welfare_id: str, db: AsyncSession = Depends(get_db)):
    w_id = _parse_uuid(welfare_id, "welfare_id")
    result = await db.execute(select(WelfareWorker).where(WelfareWorker.id == w_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="복지사를 찾을 수 없습니다.")

    # BR-003: 담당 active 회원이 있으면 삭제 불가
    active_cnt = await _active_user_count(db, worker.id)
    if active_cnt > 0:
        raise HTTPException(
            status_code=409,
            detail=f"담당 회원 {active_cnt}명이 있어 삭제할 수 없습니다. 먼저 재배정하세요.",
        )

    if worker.status == "inactive":
        raise HTTPException(status_code=409, detail="이미 비활성 처리된 복지사입니다.")

    worker.status = "inactive"
    await _record_log(db, "delete_worker", "worker", worker.id, {"name": worker.name})
    await db.commit()
    return {"welfare_id": str(worker.id), "status": "inactive"}


# ─────────────────────────────────────
# 작업 로그 + 대시보드
# ─────────────────────────────────────

@router.get("/logs", summary="관리자 작업 로그")
async def list_logs(
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 30,
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    conditions = []
    if action:
        conditions.append(AdminLog.action == action)
    if target_type:
        conditions.append(AdminLog.target_type == target_type)

    base = select(AdminLog)
    for c in conditions:
        base = base.where(c)

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0

    result = await db.execute(
        base.order_by(AdminLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(l.id),
                "admin_id": l.admin_id,
                "action": l.action,
                "target_type": l.target_type,
                "target_id": l.target_id,
                "payload": json.loads(l.payload) if l.payload else None,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/dashboard", summary="관리자 대시보드")
async def admin_dashboard(db: AsyncSession = Depends(get_db)):
    async def _count(stmt) -> int:
        return (await db.execute(stmt)).scalar() or 0

    total_users = await _count(
        select(func.count(User.id)).where(User.status != "withdrawn")
    )
    elder_cnt = await _count(
        select(func.count(User.id)).where(User.user_type == "elder", User.status != "withdrawn")
    )
    youth_cnt = await _count(
        select(func.count(User.id)).where(User.user_type == "youth", User.status != "withdrawn")
    )
    worker_cnt = await _count(
        select(func.count(WelfareWorker.id)).where(WelfareWorker.status == "active")
    )
    unresolved_alerts = await _count(
        select(func.count(SafetyAlert.id)).where(SafetyAlert.resolved == False)
    )

    # 최근 10건 작업 로그
    log_result = await db.execute(
        select(AdminLog).order_by(AdminLog.created_at.desc()).limit(10)
    )
    recent_logs = log_result.scalars().all()

    return {
        "stats": {
            "total_users": total_users,
            "elder": elder_cnt,
            "youth": youth_cnt,
            "workers": worker_cnt,
            "unresolved_alerts": unresolved_alerts,
        },
        "recent_logs": [
            {
                "id": str(l.id),
                "action": l.action,
                "target_type": l.target_type,
                "target_id": l.target_id,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in recent_logs
        ],
    }
