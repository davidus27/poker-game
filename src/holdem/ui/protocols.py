"""Interfaces implemented by table-state renderers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from holdem.domain.events import Event
from holdem.domain.views import SeatView


class View(Protocol):
    """Render engine events and a seat-private state snapshot."""

    def render(self, events: Sequence[Event], view: SeatView) -> None:
        """Present the latest state to a player."""
        ...
