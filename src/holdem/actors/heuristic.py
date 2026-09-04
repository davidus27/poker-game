"""Legal-action-only poker bots with configurable difficulty policies."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

from holdem.actors.strength import (
    chen_strength,
    draw_equity,
    monte_carlo_equity,
    pot_odds,
)
from holdem.domain.actions import Action, ActionKind
from holdem.domain.cards import HandRank
from holdem.domain.hands import find_best_hand
from holdem.domain.views import LegalAction, SeatView


class BotDifficulty(StrEnum):
    """Player-facing bot difficulty."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class DifficultyPolicy:
    """Tuning knobs for one heuristic playing style."""

    difficulty: BotDifficulty
    preflop_play: float
    value_raise: float
    fold_margin: float
    noise: float
    raise_pot_fraction: float
    use_draws: bool
    monte_carlo_samples: int
    button_bonus: float
    out_of_position_penalty: float
    calling_floor: float = 0.0
    short_stack_blinds: float = 4.0


_POLICIES = {
    BotDifficulty.EASY: DifficultyPolicy(
        difficulty=BotDifficulty.EASY,
        preflop_play=6.0,
        value_raise=0.95,
        fold_margin=0.55,
        noise=0.20,
        raise_pot_fraction=0.0,
        use_draws=False,
        monte_carlo_samples=0,
        button_bonus=0.0,
        out_of_position_penalty=0.0,
        calling_floor=0.08,
    ),
    BotDifficulty.MEDIUM: DifficultyPolicy(
        difficulty=BotDifficulty.MEDIUM,
        preflop_play=10.0,
        value_raise=0.58,
        fold_margin=1.0,
        noise=0.08,
        raise_pot_fraction=0.5,
        use_draws=True,
        monte_carlo_samples=0,
        button_bonus=0.03,
        out_of_position_penalty=0.0,
    ),
    BotDifficulty.HARD: DifficultyPolicy(
        difficulty=BotDifficulty.HARD,
        preflop_play=12.0,
        value_raise=0.64,
        fold_margin=1.15,
        noise=0.03,
        raise_pot_fraction=0.75,
        use_draws=True,
        monte_carlo_samples=80,
        button_bonus=0.08,
        out_of_position_penalty=0.03,
    ),
}

_MADE_HAND_FLOORS = {
    HandRank.HIGH_CARD: 0.12,
    HandRank.PAIR: 0.38,
    HandRank.TWO_PAIR: 0.58,
    HandRank.THREE_OF_A_KIND: 0.68,
    HandRank.STRAIGHT: 0.78,
    HandRank.FLUSH: 0.82,
    HandRank.FULL_HOUSE: 0.91,
    HandRank.FOUR_OF_A_KIND: 0.97,
    HandRank.STRAIGHT_FLUSH: 0.99,
    HandRank.ROYAL_FLUSH: 1.0,
}


def policy_for(difficulty: BotDifficulty | str) -> DifficultyPolicy:
    """Return the immutable policy for ``difficulty``."""

    try:
        parsed = BotDifficulty(difficulty)
    except ValueError as error:
        choices = ", ".join(item.value for item in BotDifficulty)
        raise ValueError(f"unknown bot difficulty {difficulty!r}; choose {choices}") from error
    return _POLICIES[parsed]


@dataclass
class HeuristicBot:
    """Estimate hand value, then materialize one of the supplied legal actions."""

    policy: DifficultyPolicy = field(default_factory=lambda: policy_for(BotDifficulty.MEDIUM))
    rng: random.Random = field(default_factory=random.Random)

    def decide(self, view: SeatView) -> Action:
        if not view.legal_actions:
            raise ValueError(f"seat {view.seat_id} has no legal actions")

        legal = {choice.kind: choice for choice in view.legal_actions}
        equity = self._estimated_equity(view)
        equity = min(1.0, max(0.0, equity + self.rng.uniform(-self.policy.noise, self.policy.noise)))
        odds = pot_odds(view)

        if odds == 0:
            if equity >= self._raise_threshold(view):
                aggressive = self._aggressive_action(view, legal)
                if aggressive is not None:
                    return aggressive
            if ActionKind.CHECK in legal:
                return Action.check()
            return self._materialize(view, view.legal_actions[0])

        if equity < odds * self.policy.fold_margin and ActionKind.FOLD in legal:
            return Action.fold()

        if equity >= self._raise_threshold(view):
            aggressive = self._aggressive_action(view, legal)
            if aggressive is not None:
                return aggressive

        if ActionKind.CALL in legal:
            return Action.call()
        if ActionKind.CHECK in legal:
            return Action.check()
        return self._materialize(view, view.legal_actions[0])

    def _estimated_equity(self, view: SeatView) -> float:
        if not view.board:
            equity = max(chen_strength(view.hole), self.policy.calling_floor)
        elif self.policy.monte_carlo_samples:
            equity = monte_carlo_equity(
                view,
                self.rng,
                samples=self.policy.monte_carlo_samples,
            )
        else:
            rank = find_best_hand(list(view.board), list(view.hole)).rank
            equity = _MADE_HAND_FLOORS[rank]
            if self.policy.use_draws:
                equity += draw_equity(view.hole, view.board)

        if view.seat_id == view.button:
            equity += self.policy.button_bonus
        else:
            equity -= self.policy.out_of_position_penalty
        return min(1.0, max(0.0, equity))

    def _raise_threshold(self, view: SeatView) -> float:
        if not view.board:
            return max(self.policy.value_raise, self.policy.preflop_play / 20.0)
        return self.policy.value_raise

    def _aggressive_action(
        self,
        view: SeatView,
        legal: dict[ActionKind, LegalAction],
    ) -> Action | None:
        raise_choice = legal.get(ActionKind.RAISE)
        all_in = legal.get(ActionKind.ALL_IN)
        seat = next((seat for seat in view.seats if seat.seat_id == view.seat_id), None)
        short_stack = (
            seat is not None and seat.stack <= self.policy.short_stack_blinds * view.big_blind
        )

        if all_in is not None and (short_stack or raise_choice is None):
            return Action.all_in()
        if raise_choice is None:
            return None
        if raise_choice.min_amount is None or raise_choice.max_amount is None:
            raise ValueError("legal raise must include minimum and maximum amounts")
        if raise_choice.min_amount > raise_choice.max_amount:
            raise ValueError("legal raise minimum exceeds maximum")

        desired = view.current_bet + round(view.pot_total * self.policy.raise_pot_fraction)
        amount = min(raise_choice.max_amount, max(raise_choice.min_amount, desired))
        if all_in is not None and amount == raise_choice.max_amount:
            return Action.all_in()
        return Action.raise_to(amount)

    @staticmethod
    def _materialize(view: SeatView, legal: LegalAction) -> Action:
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
            return Action.raise_to(legal.min_amount)
        raise ValueError(f"unsupported legal action for seat {view.seat_id}: {legal.kind}")


def make_bot(
    difficulty: BotDifficulty | str = BotDifficulty.MEDIUM,
    rng: random.Random | None = None,
) -> HeuristicBot:
    """Build a heuristic bot, defaulting to medium difficulty."""

    return HeuristicBot(policy_for(difficulty), rng or random.Random())
