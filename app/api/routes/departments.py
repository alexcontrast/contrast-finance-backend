from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentRead


router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db)):
    result = db.execute(select(Department).order_by(Department.id))
    return result.scalars().all()


@router.post("", response_model=DepartmentRead)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    department = Department(
        name=payload.name,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.post("/seed", response_model=list[DepartmentRead])
def seed_departments(db: Session = Depends(get_db)):
    """
    Creates the default Contrast departments:
    - Санжар
    - Рауфаль

    Safe to run multiple times.
    """
    default_names = ["Санжар", "Рауфаль"]

    existing_result = db.execute(select(Department).where(Department.name.in_(default_names)))
    existing = {department.name: department for department in existing_result.scalars().all()}

    for name in default_names:
        if name not in existing:
            db.add(
                Department(
                    name=name,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

    db.commit()

    result = db.execute(select(Department).order_by(Department.id))
    return result.scalars().all()
