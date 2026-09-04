"""Fold-wins, split pots, heads-up, bust-out, tournament end."""

from __future__ import annotations

import pytest

from holdem.domain.actions import Action
from holdem.domain.events import (
    HandEnded,
    PlayerBusted,
    PotsAwarded,
    Showdown,
    TournamentEnded,
)
from holdem.domain.views import Street
from holdem.engine.exceptions import EngineStateError
from holdem.engine.table import Table
from tests.engine.helpers import build_deck, play_script


def test_fold_wins_without_showdown() -> None:
    table = Table(stacks=[200, 200, 200], small_blind=5, big_blind=10)
    events = play_script(
        table,
        {
            0: [Action.fold()],
            1: [Action.fold()],
        },
    )
    assert not any(isinstance(e, Showdown) for e in events)
    awarded = next(e for e in events if isinstance(e, PotsAwarded))
    assert awarded.awards[0].winners == (2,)
    assert table.board == ()
    # uncalled portion of the BB is returned; BB wins the SB's 5
    assert table.stacks_now() == (200, 195, 205)


def test_split_pot_on_identical_hand_score() -> None:
    # Both play the board: broadway straight, identical kickers.
    cards = build_deck(
        2,
        button=0,
        holes={0: "2c 3c", 1: "2d 3d"},
        board="As Ks Qs Js Ts",
    )
    table = Table(stacks=[100, 100], small_blind=5, big_blind=10)
    events = play_script(
        table,
        {
            0: [Action.call(), Action.check(), Action.check(), Action.check()],
            1: [Action.check(), Action.check(), Action.check(), Action.check()],
        },
        cards=cards,
    )
    showdown = next(e for e in events if isinstance(e, Showdown))
    assert showdown.revelations[0].score == showdown.revelations[1].score
    awarded = next(e for e in events if isinstance(e, PotsAwarded))
    assert set(awarded.awards[0].winners) == {0, 1}
    assert awarded.awards[0].shares == (10, 10)
    assert table.stacks_now() == (100, 100)


def test_heads_up_showdown_awards_winner() -> None:
    cards = build_deck(
        2,
        button=0,
        holes={0: "As Ah", 1: "Kc Kd"},
        board="2s 3h 7d 8c 9s",
    )
    table = Table(stacks=[100, 100], small_blind=5, big_blind=10)
    events = play_script(
        table,
        {
            0: [Action.call(), Action.check(), Action.check(), Action.check()],
            1: [Action.check(), Action.check(), Action.check(), Action.check()],
        },
        cards=cards,
    )
    awarded = next(e for e in events if isinstance(e, PotsAwarded))
    assert awarded.awards[0].winners == (0,)
    assert table.stacks_now() == (110, 90)


def test_bust_and_tournament_end() -> None:
    cards = build_deck(
        2,
        button=0,
        holes={0: "As Ah", 1: "Kc Kd"},
        board="2s 3h 7d 8c 9s",
    )
    table = Table(stacks=[50, 50], small_blind=5, big_blind=10)
    events = play_script(
        table,
        {
            0: [Action.all_in()],
            1: [Action.call()],
        },
        cards=cards,
    )
    assert any(isinstance(e, PlayerBusted) and e.seat_id == 1 for e in events)
    ended = next(e for e in events if isinstance(e, TournamentEnded))
    assert ended.winner == 0
    assert table.is_tournament_over
    assert table.street is Street.TOURNAMENT_OVER
    assert table.stacks_now() == (100, 0)
    with pytest.raises(EngineStateError):
        table.start_hand()


def test_hand_ended_event_emitted() -> None:
    table = Table(stacks=[200, 200, 200])
    events = play_script(table, {0: [Action.fold()], 1: [Action.fold()]})
    assert any(isinstance(e, HandEnded) for e in events)


def test_seat_view_hides_foreign_hole_cards() -> None:
    cards = build_deck(
        3,
        button=0,
        holes={0: "As Ah", 1: "Ks Kh", 2: "Qs Qh"},
        board="2c 3d 7h 8s 9c",
    )
    table = Table(stacks=[200, 200, 200])
    table.start_hand(cards=cards)
    view0 = table.seat_view(0)
    view1 = table.seat_view(1)
    assert view0.hole[0].rank != view1.hole[0].rank or view0.hole[1] != view1.hole[1]
    assert len(view0.hole) == 2
    # public seats never include hole cards
    assert not hasattr(view0.seats[1], "hole")
