"""Behavioral and legality tests for player-facing heuristic bots."""

from __future__ import annotations

import random
from dataclasses import replace

import pytest

from holdem.actors import BotDifficulty, HeuristicBot, make_bot, policy_for
from holdem.domain import (
    ActionKind,
    LegalAction,
    PublicSeat,
    SeatStatus,
    SeatView,
    Street,
    parse_cards,
)
from holdem.engine import Table


def _view(
    *,
    hole: str = "7s 2h",
    button: int = 1,
    hero_bet: int = 10,
    current_bet: int = 20,
    pot_total: int = 90,
    legal_actions: tuple[LegalAction, ...] = (
        LegalAction(ActionKind.FOLD),
        LegalAction(ActionKind.CALL),
    ),
) -> SeatView:
    return SeatView(
        seat_id=0,
        street=Street.PREFLOP,
        hand_number=1,
        button=button,
        small_blind=5,
        big_blind=10,
        board=(),
        hole=parse_cards(hole),
        pot_total=pot_total,
        pots=(),
        seats=(
            PublicSeat(
                seat_id=0,
                stack=100,
                status=SeatStatus.ACTIVE,
                street_bet=hero_bet,
                committed=hero_bet,
            ),
            PublicSeat(
                seat_id=1,
                stack=100,
                status=SeatStatus.ACTIVE,
                street_bet=current_bet,
                committed=current_bet,
            ),
        ),
        to_act=0,
        legal_actions=legal_actions,
        current_bet=current_bet,
        min_raise_to=40,
    )


def _deterministic_bot(difficulty: BotDifficulty) -> HeuristicBot:
    return HeuristicBot(replace(policy_for(difficulty), noise=0.0), random.Random(7))


def test_easy_calls_priced_junk_that_medium_and_hard_fold() -> None:
    view = _view()

    assert _deterministic_bot(BotDifficulty.EASY).decide(view).kind is ActionKind.CALL
    assert _deterministic_bot(BotDifficulty.MEDIUM).decide(view).kind is ActionKind.FOLD
    assert _deterministic_bot(BotDifficulty.HARD).decide(view).kind is ActionKind.FOLD


def test_hard_uses_position_when_junk_is_cheap() -> None:
    out_of_position = _view(pot_total=190)
    on_button = _view(button=0, pot_total=190)
    bot = _deterministic_bot(BotDifficulty.HARD)

    assert bot.decide(out_of_position).kind is ActionKind.FOLD
    assert bot.decide(on_button).kind is ActionKind.CALL


@pytest.mark.parametrize("difficulty", list(BotDifficulty))
def test_every_difficulty_only_materializes_supplied_actions(
    difficulty: BotDifficulty,
) -> None:
    legal = (
        LegalAction(ActionKind.FOLD),
        LegalAction(ActionKind.CALL),
        LegalAction(ActionKind.RAISE, min_amount=40, max_amount=75),
        LegalAction(ActionKind.ALL_IN),
    )
    bot = make_bot(difficulty, random.Random(42))

    for _ in range(200):
        action = bot.decide(_view(hole="As Ah", legal_actions=legal))
        assert action.kind in {choice.kind for choice in legal}
        if action.kind is ActionKind.RAISE:
            assert action.amount is not None
            assert 40 <= action.amount <= 75


def test_heuristic_bot_rejects_view_without_legal_actions() -> None:
    with pytest.raises(ValueError, match="seat 0 has no legal actions"):
        make_bot(rng=random.Random(0)).decide(_view(legal_actions=()))


def test_heuristic_bots_can_run_a_tournament_to_a_winner() -> None:
    table = Table([40, 40, 40], small_blind=5, big_blind=10, rng=random.Random(3))
    bots = {seat: make_bot(BotDifficulty.MEDIUM, random.Random(seat)) for seat in range(3)}

    decisions = 0
    hands = 0
    while not table.is_tournament_over:
        table.start_hand()
        hands += 1
        while table.to_act is not None:
            seat = table.to_act
            table.apply(bots[seat].decide(table.seat_view(seat)))
            decisions += 1
            assert decisions < 5_000
        assert hands < 1_000

    assert sum(stack > 0 for stack in table.stacks_now()) == 1
