"""Constructor validation, illegal engine transitions, incomplete raises."""

from __future__ import annotations

import pytest

from holdem.domain.actions import Action, ActionKind
from holdem.domain.events import Showdown
from holdem.engine.exceptions import EngineStateError
from holdem.engine.pots import build_pots, return_uncalled
from holdem.engine.table import Table


def test_table_rejects_invalid_config() -> None:
    with pytest.raises(ValueError):
        Table(stacks=[100])
    with pytest.raises(ValueError):
        Table(stacks=[100, 100], small_blind=0)
    with pytest.raises(ValueError):
        Table(stacks=[100, 100], small_blind=20, big_blind=10)
    with pytest.raises(ValueError):
        Table(stacks=[100, -1])


def test_raise_to_rejects_non_positive() -> None:
    with pytest.raises(ValueError):
        Action.raise_to(0)


def test_cannot_start_with_fewer_than_two_live_stacks() -> None:
    table = Table(stacks=[100, 0])
    with pytest.raises(EngineStateError):
        table.start_hand()


def test_cannot_start_hand_while_one_is_in_progress() -> None:
    table = Table(stacks=[100, 100])
    table.start_hand()
    with pytest.raises(EngineStateError):
        table.start_hand()


def test_unknown_seat_view_rejected() -> None:
    table = Table(stacks=[100, 100])
    with pytest.raises(ValueError):
        table.seat_view(5)


def test_both_blinds_all_in_runs_out_board() -> None:
    table = Table(stacks=[5, 10], small_blind=5, big_blind=10)
    events = table.start_hand()
    assert table.to_act is None
    assert table.is_hand_over
    assert any(isinstance(e, Showdown) for e in events)
    assert len(table.board) == 5


def test_incomplete_all_in_does_not_reopen_raiser() -> None:
    table = Table(stacks=[200, 40, 200], small_blind=5, big_blind=10)
    table.start_hand()
    table.apply(Action.raise_to(30))
    table.apply(Action.all_in())
    assert table.seat_view(2).current_bet == 40
    kinds_bb = {a.kind for a in table.seat_view(2).legal_actions}
    assert ActionKind.RAISE in kinds_bb
    table.apply(Action.call())
    assert table.to_act == 0
    kinds_opener = {a.kind for a in table.seat_view(0).legal_actions}
    assert ActionKind.RAISE not in kinds_opener
    assert ActionKind.CALL in kinds_opener
    assert ActionKind.FOLD in kinds_opener


def test_build_pots_empty_and_single_contributor() -> None:
    assert build_pots({}, set()) == []
    assert return_uncalled({0: 10}) == {0: 10}
