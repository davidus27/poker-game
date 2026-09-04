"""Interfaces implemented by decision-making actors and human input adapters."""

from __future__ import annotations

from typing import Protocol

from holdem.domain.actions import Action
from holdem.domain.views import SeatView


class Actor(Protocol):
    """A source of decisions for one poker seat."""

    def decide(self, view: SeatView) -> Action:
        """Choose an action from the legal choices in ``view``."""
        ...


class ActionSource(Protocol):
    """Injected input boundary used by a local human actor."""

    def __call__(self, view: SeatView) -> Action:
        """Collect and return the human's next action."""
        ...
