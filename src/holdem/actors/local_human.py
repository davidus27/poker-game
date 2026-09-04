"""Local human actor with input supplied by an adapter."""

from __future__ import annotations

from dataclasses import dataclass

from holdem.actors.protocols import ActionSource
from holdem.domain.actions import Action
from holdem.domain.views import SeatView


@dataclass(frozen=True)
class LocalHuman:
    """Delegate decisions to injected I/O without coupling actors to a UI."""

    source: ActionSource

    def decide(self, view: SeatView) -> Action:
        return self.source(view)
