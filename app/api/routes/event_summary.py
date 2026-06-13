from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.models.event_item import EventItem
from app.models.user import User
from app.schemas.event_summary import EventSummaryRead
from app.services.event_calculator import calculate_event_summary_values, q
from app.services.auth import get_current_user
from app.services.authorization import require_event_view


router = APIRouter(tags=["event_summary"])


@router.get("/events/{event_id}/summary", response_model=EventSummaryRead)
def get_event_summary(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    require_event_view(current_user, event, db)

    result = db.execute(
        select(EventItem)
        .where(EventItem.event_id == event_id, EventItem.is_deleted == False)  # noqa: E712
        .order_by(EventItem.sort_order, EventItem.id)
    )
    items = result.scalars().all()

    values = calculate_event_summary_values(event, items)

    return EventSummaryRead(
        event_id=event.id,
        client_name=event.client_name,
        title=event.title,
        status=event.status,
        client_calc_type=event.client_calc_type,

        external_total=q(values["external_total"]),
        fact_total=q(values["fact_total"]),
        paid_total=q(values["paid_total"]),
        customer_paid_amount=q(getattr(event, "customer_paid_amount", 0) or 0),
        customer_remaining_amount=q(max(Decimal("0.00"), values["turnover_with_vat"] - (getattr(event, "customer_paid_amount", 0) or 0))),

        regular_external_total=q(values["regular_external_total"]),
        regular_fact_total=q(values["regular_fact_total"]),

        coordinator_external_total=q(values["coordinator_external_total"]),
        coordinator_fact_amount=q(values["coordinator_fact_amount"]),
        coordinator_company_share=q(values["coordinator_company_share"]),

        vat_total=q(values["vat_total"]),
        deductions_total=q(values["deductions_total"]),

        internal_tax_amount=q(values["internal_tax_amount"]),
        simplified_bank_tax_amount=q(values["simplified_bank_tax_amount"]),

        manager_salary_base=q(values["manager_salary_base"]),
        manager_percent=q(values["manager_percent"]),
        manager_salary=q(values["manager_salary"]),
        manager_salary_paid=q(values["manager_salary_paid"]),

        company_income_before_manager_salary=q(values["company_income_before_manager_salary"]),
        company_income_after_manager_salary=q(values["company_income_after_manager_salary"]),
        final_company_income=q(values["final_company_income"]),

        turnover_with_vat=q(values["turnover_with_vat"]),
        client_vat_amount=q(values["client_vat_amount"]),
        contractor_vat_credit=q(values["contractor_vat_credit"]),
        vat_to_pay=q(values["vat_to_pay"]),
        tax_rate_percent=q(values["tax_rate_percent"]),
        tax_base_amount=q(values["tax_base_amount"]),
        taxes_total=q(values["taxes_total"]),
    )
