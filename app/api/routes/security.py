from fastapi import APIRouter, Depends

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
