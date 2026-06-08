from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.models.user import User
from app.schemas.security import SecurityCheckRead
from app.services.auth import get_current_user, require_roles


router = APIRouter(tags=["security"])


@router.get("/security/whoami", response_model=SecurityCheckRead)
def security_whoami(user: User = Depends(get_current_user)):
    return SecurityCheckRead(
        ok=True,
        user_id=user.id,
        role=user.role,
        department_id=user.department_id,
    )


@router.get("/security/admin-only", response_model=SecurityCheckRead)
def security_admin_only(user: User = Depends(require_roles("admin"))):
    return SecurityCheckRead(
        ok=True,
        user_id=user.id,
        role=user.role,
        department_id=user.department_id,
    )



@router.get("/security/can-view-event/{event_id}")
def security_can_view_event(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.services.authorization import can_view_event, get_event_or_404
    event = get_event_or_404(db, event_id)
    return {
        "ok": can_view_event(user, event),
        "user_id": user.id,
        "role": user.role,
        "department_id": user.department_id,
        "event_id": event.id,
        "event_manager_id": event.manager_id,
        "event_department_id": event.department_id,
    }
