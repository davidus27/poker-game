"""Actor protocol implementations and legal random decisions."""

from __future__ import annotations

import random

import pytest

from holdem.actors import Actor, LocalHuman, RandomBot, ScriptedActor
from holdem.domain import Action, ActionKind, LegalAction, SeatView, Street
from holdem.engine import Table


def _view(*legal_actions: LegalAction) -> SeatView:
    return SeatView(
        seat_id=0,
        street=Street.PREFLOP,
        hand_number=1,
        button=2,
        small_blind=5,
        big_blind=10,
        board=(),
        hole=(),
        pot_total=15,
        pots=(),
        seats=(),
        to_act=0,
        legal_actions=legal_actions,
        current_bet=10,
        min_raise_to=20,
    )


def _accepts_actor(actor: Actor) -> Actor:
    return actor


def test_local_human_delegates_to_injected_action_source() -> None:
    seen: list[SeatView] = []
    view = _view(LegalAction(ActionKind.CHECK))

    def source(received: SeatView) -> Action:
        seen.append(received)
        return Action.check()

    actor = _accepts_actor(LocalHuman(source))

    assert actor.decide(view) == Action.check()
    assert seen == [view]


def test_scripted_actor_returns_actions_in_order() -> None:
    actor = ScriptedActor([Action.call(), Action.fold()])
    view = _view(LegalAction(ActionKind.CALL))

    assert _accepts_actor(actor) is actor
    assert actor.decide(view) == Action.call()
    assert actor.remaining == 1
    assert actor.decide(view) == Action.fold()

    with pytest.raises(AssertionError, match="seat 0 has no scripted action left"):
        actor.decide(view)


def test_random_bot_only_materializes_provided_legal_actions() -> None:
    legal = (
        LegalAction(ActionKind.FOLD),
        LegalAction(ActionKind.CALL),
        LegalAction(ActionKind.RAISE, min_amount=20, max_amount=75),
        LegalAction(ActionKind.ALL_IN),
    )
    bot = RandomBot(random.Random(42))

    for _ in range(200):
        action = bot.decide(_view(*legal))
        assert action.kind in {choice.kind for choice in legal}
        if action.kind == ActionKind.RAISE:
            assert action.amount is not None
            assert 20 <= action.amount <= 75


def test_random_bot_rejects_a_view_without_legal_actions() -> None:
    with pytest.raises(ValueError, match="seat 0 has no legal actions"):
        RandomBot(random.Random(0)).decide(_view())


def test_random_bots_can_drive_a_hand_using_only_seat_views() -> None:
    table = Table([100, 100, 100], rng=random.Random(1))
    bots = {seat: RandomBot(random.Random(seat)) for seat in range(3)}
    table.start_hand()

    decisions = 0
    while table.to_act is not None:
        seat = table.to_act
        table.apply(bots[seat].decide(table.seat_view(seat)))
        decisions += 1
        assert decisions < 100

    assert table.is_hand_over
