from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime
import hashlib

from app.database import get_db
from app.models.models import User, WelfareWorker

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    user_type: str
    nickname: str
    name: str | None = None
    welfare_id: str | None = None


@router.post("/login", summary="로그인 (이메일 + 비밀번호)")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    pw_hash = _hash_password(body.password)

    # 1. WelfareWorker 테이블에서 먼저 조회 (admin / worker)
    result = await db.execute(
        select(WelfareWorker).where(
            WelfareWorker.email == body.email,
            WelfareWorker.password_hash == pw_hash,
        )
    )
    worker = result.scalar_one_or_none()
    if worker:
        worker.updated_at = datetime.utcnow()
        await db.commit()
        return LoginResponse(
            user_id=str(worker.id),
            user_type=worker.role,  # "admin" | "worker"
            nickname=worker.name,
            name=worker.name,
            welfare_id=str(worker.id) if worker.role == "worker" else None,
        )

    # 2. User 테이블에서 조회 (elder / youth)
    result = await db.execute(
        select(User).where(
            User.email == body.email,
            User.password_hash == pw_hash,
        )
    )
    user = result.scalar_one_or_none()
    if user:
        user.last_seen_at = datetime.utcnow()
        await db.commit()
        return LoginResponse(
            user_id=str(user.id),
            user_type=user.user_type,
            nickname=user.nickname or "",
            name=user.name,
            welfare_id=str(user.welfare_id) if user.welfare_id else None,
        )

    raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 일치하지 않습니다.")


@router.get("/accounts", summary="시드 계정 목록 (로그인 화면용)")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    workers = (await db.execute(select(WelfareWorker))).scalars().all()
    users = (await db.execute(select(User))).scalars().all()

    items = []
    for w in workers:
        items.append({
            "user_id": str(w.id),
            "name": w.name,
            "email": w.email,
            "user_type": w.role,
            "group": "admin" if w.role == "admin" else "worker",
        })
    for u in users:
        items.append({
            "user_id": str(u.id),
            "name": u.nickname or u.name,
            "email": u.email,
            "user_type": u.user_type,
            "group": u.user_type,
        })
    return items
