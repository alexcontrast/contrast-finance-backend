from decimal import Decimal

from app.models.event import Event


MAX_EVENT_PARTICIPANTS = 3


def ordered_event_participant_ids(event: Event) -> list[int]:
    """Return unique participant ids with the primary manager first."""
    participant_ids: list[int] = []

    def append(user_id: int | None) -> None:
        if user_id is None:
            return
        normalized = int(user_id)
        if normalized not in participant_ids:
            participant_ids.append(normalized)

    append(event.manager_id)
    shares = sorted(
        list(event.shares or []),
        key=lambda share: (
            0 if int(share.user_id) == int(event.manager_id) else 1,
            int(share.id or 0),
            int(share.user_id),
        ),
    )
    for share in shares:
        append(share.user_id)

    return participant_ids


def equal_event_share_allocations(participant_ids: list[int]) -> list[tuple[int, Decimal]]:
    """Split 100.00% exactly and give any rounding remainder to the owner."""
    unique_ids: list[int] = []
    for user_id in participant_ids:
        normalized = int(user_id)
        if normalized not in unique_ids:
            unique_ids.append(normalized)

    if not unique_ids:
        return []
    if len(unique_ids) > MAX_EVENT_PARTICIPANTS:
        raise ValueError(f"An event can have at most {MAX_EVENT_PARTICIPANTS} managers")

    total_hundredths = 10_000
    base_hundredths = total_hundredths // len(unique_ids)
    remainder = total_hundredths - base_hundredths * len(unique_ids)

    result: list[tuple[int, Decimal]] = []
    for index, user_id in enumerate(unique_ids):
        hundredths = base_hundredths + (remainder if index == 0 else 0)
        result.append((user_id, Decimal(hundredths) / Decimal("100")))
    return result
