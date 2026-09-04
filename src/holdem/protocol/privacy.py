"""Recipient-specific filtering for engine events."""

from __future__ import annotations

from collections.abc import Iterable

from holdem.domain.events import Event, HoleDealt


def events_for_seat(events: Iterable[Event], seat_id: int) -> tuple[Event, ...]:
    """Hide other players' private deal events before transmission."""

    return tuple(
        event for event in events if not isinstance(event, HoleDealt) or event.seat_id == seat_id
    )
