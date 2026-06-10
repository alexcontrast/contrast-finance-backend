from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.app_bootstrap import (
    AppBootstrapRead,
    DepartmentOptionRead,
    EconomicsSettingsBootstrapRead,
)
from app.schemas.auth import AuthPermissionsRead, AuthUserRead
from app.services.auth import get_current_user


router = APIRouter(tags=["app"])


def month_start_today() -> date:
    today = date.today()
    return date(today.year, today.month, 1)


def user_to_read(user: User) -> AuthUserRead:
    return AuthUserRead(
        id=user.id,
        name=user.name,
        phone=user.phone,
        email=user.email,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        role=user.role,
        is_active=user.is_active,
        legacy_user_id=user.legacy_user_id,
        auth_source=user.auth_source or "legacy_apps_script",
    )


def permissions_for_user(user: User) -> AuthPermissionsRead:
    return AuthPermissionsRead(
        role=user.role,
        department_id=user.department_id,
        can_view_admin_dashboard=user.role == "admin",
        can_manage_users=user.role == "admin",
        can_view_department_dashboard=user.role in {"admin", "department_head"},
        can_edit=user.role in {"admin", "manager"},
    )


def default_screen_for_role(role: str) -> str:
    if role == "admin":
        return "admin_dashboard"
    if role == "department_head":
        return "department_head_dashboard"
    if role == "manager":
        return "manager_dashboard"
    if role == "accountant":
        return "admin_dashboard"
    return "manager_dashboard"


@router.get("/app/bootstrap", response_model=AppBootstrapRead)
def app_bootstrap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()

    departments = db.execute(
        select(Department).where(Department.is_active == True).order_by(Department.id)  # noqa: E712
    ).scalars().all()

    return AppBootstrapRead(
        user=user_to_read(current_user),
        permissions=permissions_for_user(current_user),
        departments=[
            DepartmentOptionRead(
                id=department.id,
                name=department.name,
                is_active=department.is_active,
            )
            for department in departments
        ],
        active_month=month_start_today(),
        economics=EconomicsSettingsBootstrapRead(
            vat_rate=settings.VAT_RATE,
            contractor_deduction_rate=settings.CONTRACTOR_DEDUCTION_RATE,
            contrast_internal_tax_rate=settings.CONTRAST_INTERNAL_TAX_RATE,
            simplified_tax_rate=settings.SIMPLIFIED_TAX_RATE,
        ),
        default_screen=default_screen_for_role(current_user.role),
    )
