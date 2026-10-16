from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.services.auth import require_roles


router = APIRouter(prefix="/users-legacy", tags=["users_legacy"])


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    result = db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.post("", response_model=UserRead)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    user = User(
        department_id=payload.department_id,
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        telegram_id=payload.telegram_id,
        telegram_username=payload.telegram_username,
        role=payload.role,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
