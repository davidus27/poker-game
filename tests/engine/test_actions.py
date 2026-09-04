"""Call, raise, reraise, fold, check, and illegal-action rejection."""

from __future__ import annotations

import pytest

from holdem.domain.actions import Action, ActionKind
from holdem.domain.events import PlayerActed
from holdem.domain.views import Street
from holdem.engine.exceptions import IllegalAction
from holdem.engine.table import Table


def _three() -> Table:
    table = Table(stacks=[200, 200, 200], small_blind=5, big_blind=10)
    table.start_hand()
    return table


def test_check_not_legal_when_facing_a_bet() -> None:
    table = _three()
    kinds = {a.kind for a in table.seat_view(0).legal_actions}
    assert ActionKind.CHECK not in kinds
    assert ActionKind.FOLD in kinds
    assert ActionKind.CALL in kinds
    with pytest.raises(IllegalAction):
        table.apply(Action.check())


def test_call_matches_the_big_blind() -> None:
    table = _three()
    events = table.apply(Action.call())
    acted = next(e for e in events if isinstance(e, PlayerActed))
    assert acted.chips == 10
    assert acted.street_bet == 10
    assert table.seat_view(0).seats[0].stack == 190


def test_raise_and_reraise() -> None:
    table = _three()
    # seat 0 raises to 30
    table.apply(Action.raise_to(30))
    assert table.seat_view(1).current_bet == 30
    view = table.seat_view(1)
    raise_opt = next(a for a in view.legal_actions if a.kind is ActionKind.RAISE)
    assert raise_opt.min_amount == 50  # last increment was 20
    table.apply(Action.raise_to(50))
    assert table.to_act == 2
    table.apply(Action.raise_to(90))
    assert table.seat_view(0).current_bet == 90


def test_fold_removes_seat_from_hand() -> None:
    table = _three()
    table.apply(Action.fold())
    assert table.seat_view(0).seats[0].status.value == "folded"
    assert table.to_act == 1


def test_check_around_advances_street() -> None:
    table = Table(stacks=[100, 100], small_blind=5, big_blind=10)
    table.start_hand()
    table.apply(Action.call())
    table.apply(Action.check())
    assert table.street == Street.FLOP
    table.apply(Action.check())
    table.apply(Action.check())
    assert table.street == Street.TURN
    table.apply(Action.check())
    table.apply(Action.check())
    assert table.street == Street.RIVER
    table.apply(Action.check())
    table.apply(Action.check())
    assert table.is_hand_over


def test_raise_below_minimum_is_rejected() -> None:
    table = _three()
    with pytest.raises(IllegalAction):
        table.apply(Action.raise_to(15))
    with pytest.raises(IllegalAction):
        table.apply(Action.raise_to(11))


def test_action_out_of_turn_is_rejected() -> None:
    table = _three()
    # seat 1 is not to act
    assert table.to_act == 0
    # applying is always for to_act; out-of-turn is "no way to apply for another seat"
    # folding a check-like no-op from the wrong semantic: illegal check
    table.apply(Action.fold())
    assert table.to_act == 1
    with pytest.raises(IllegalAction):
        table.apply(Action.check())


def test_apply_when_nobody_to_act_is_rejected() -> None:
    table = Table(stacks=[100, 100])
    with pytest.raises(IllegalAction):
        table.apply(Action.check())


def test_min_raise_to_is_two_big_blinds_preflop() -> None:
    table = _three()
    view = table.seat_view(0)
    raise_opt = next(a for a in view.legal_actions if a.kind is ActionKind.RAISE)
    assert raise_opt.min_amount == 20
    assert raise_opt.max_amount == 200
