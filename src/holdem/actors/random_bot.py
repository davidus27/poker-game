"""Bot that samples exclusively from the engine's legal actions."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from holdem.domain.actions import Action, ActionKind
from holdem.domain.views import LegalAction, SeatView


@dataclass
class RandomBot:
    """Choose a legal action and, for raises, a legal raise-to amount."""

    rng: random.Random = field(default_factory=random.Random)

    def decide(self, view: SeatView) -> Action:
        if not view.legal_actions:
            raise ValueError(f"seat {view.seat_id} has no legal actions")
        return self._to_action(self.rng.choice(view.legal_actions))

    def _to_action(self, legal: LegalAction) -> Action:
        if legal.kind == ActionKind.FOLD:
            return Action.fold()
        if legal.kind == ActionKind.CHECK:
            return Action.check()
        if legal.kind == ActionKind.CALL:
            return Action.call()
        if legal.kind == ActionKind.ALL_IN:
            return Action.all_in()
        if legal.kind == ActionKind.RAISE:
            if legal.min_amount is None or legal.max_amount is None:
                raise ValueError("legal raise must include minimum and maximum amounts")
            if legal.min_amount > legal.max_amount:
                raise ValueError("legal raise minimum exceeds maximum")
            return Action.raise_to(self.rng.randint(legal.min_amount, legal.max_amount))
        raise ValueError(f"unsupported legal action: {legal.kind}")
