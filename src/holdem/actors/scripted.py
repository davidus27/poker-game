"""Deterministic actor for tests, examples, and engine replays."""

from __future__ import annotations

from collections.abc import Iterable

from holdem.domain.actions import Action
from holdem.domain.views import SeatView


class ScriptedActor:
    """Return a predetermined sequence of actions."""

    def __init__(self, actions: Iterable[Action]) -> None:
        self._actions = tuple(actions)
        self._index = 0

    def decide(self, view: SeatView) -> Action:
        if self._index >= len(self._actions):
            raise AssertionError(f"seat {view.seat_id} has no scripted action left")
        action = self._actions[self._index]
        self._index += 1
        return action

    @property
    def remaining(self) -> int:
        """Number of actions that have not been returned yet."""
        return len(self._actions) - self._index
