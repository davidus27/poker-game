"""Side pots: two layers, three layers, and uncalled-bet return."""

from __future__ import annotations

from holdem.domain.actions import Action
from holdem.domain.events import PotsAwarded, Showdown
from holdem.engine.pots import Pot, build_pots, return_uncalled
from holdem.engine.table import Table
from tests.engine.helpers import build_deck, play_script


def test_build_pots_two_layers() -> None:
    pots = build_pots({0: 50, 1: 100, 2: 100}, folded=set())
    assert pots == [
        Pot(amount=150, eligible=frozenset({0, 1, 2})),
        Pot(amount=100, eligible=frozenset({1, 2})),
    ]


def test_build_pots_three_layers() -> None:
    pots = build_pots({0: 20, 1: 50, 2: 80, 3: 80}, folded=set())
    assert pots == [
        Pot(amount=80, eligible=frozenset({0, 1, 2, 3})),
        Pot(amount=90, eligible=frozenset({1, 2, 3})),
        Pot(amount=60, eligible=frozenset({2, 3})),
    ]


def test_folded_player_contributes_but_cannot_win() -> None:
    pots = build_pots({0: 50, 1: 100, 2: 100}, folded={0})
    assert pots[0].amount == 150
    assert pots[0].eligible == frozenset({1, 2})


def test_return_uncalled_excess() -> None:
    assert return_uncalled({0: 50, 1: 100}) == {0: 50, 1: 50}


def test_return_uncalled_no_excess_when_tied() -> None:
    assert return_uncalled({0: 80, 1: 80}) == {0: 80, 1: 80}


def test_two_layer_side_pots_at_showdown() -> None:
    # stacks 50 / 100 / 100 — A all-in 50, B and C put 100
    # holes: seat0 wins main (AA), seat1 wins side (KK vs QQ)
    cards = build_deck(
        3,
        button=0,
        holes={0: "As Ah", 1: "Ks Kh", 2: "Qs Qh"},
        board="2c 3d 7h 8s 9c",
    )
    table = Table(stacks=[50, 100, 100], small_blind=5, big_blind=10)
    events = play_script(
        table,
        {
            0: [Action.all_in()],
            1: [Action.all_in()],
            2: [Action.call()],
        },
        cards=cards,
    )
    assert any(isinstance(e, Showdown) for e in events)
    awarded = next(e for e in events if isinstance(e, PotsAwarded))
    assert len(awarded.awards) == 2
    main, side = awarded.awards
    assert main.amount == 150
    assert main.winners == (0,)
    assert side.amount == 100
    assert side.winners == (1,)
    # 0: won 150, committed 50 → stack 150
    # 1: won 100, committed 100 → stack 100
    # 2: won 0, committed 100 → stack 0
    assert table.stacks_now() == (150, 100, 0)


def test_three_layer_side_pots_at_showdown() -> None:
    cards = build_deck(
        4,
        button=0,
        holes={0: "As Ah", 1: "Ks Kh", 2: "Qs Qh", 3: "Js Jh"},
        board="2c 3d 7h 8s 9c",
    )
    table = Table(stacks=[20, 50, 80, 80], small_blind=5, big_blind=10)
    # 4-handed: UTG is seat 3, then button 0, SB 1, BB 2
    events = play_script(
        table,
        {
            3: [Action.all_in()],
            0: [Action.all_in()],
            1: [Action.all_in()],
            2: [Action.all_in()],
        },
        cards=cards,
    )
    awarded = next(e for e in events if isinstance(e, PotsAwarded))
    amounts = [a.amount for a in awarded.awards]
    assert amounts == [80, 90, 60]
    assert awarded.awards[0].winners == (0,)
    assert awarded.awards[1].winners == (1,)
    assert awarded.awards[2].winners == (2,)


def test_uncalled_raise_returned_on_fold() -> None:
    table = Table(stacks=[200, 200], small_blind=5, big_blind=10)
    table.start_hand()
    table.apply(Action.raise_to(40))
    table.apply(Action.fold())
    # seat 0 posted SB 5 then raised to 40 (put 35 more) = 40 committed
    # seat 1 posted BB 10 and folded. Uncalled 30 returned to seat 0.
    # pot = 10 (BB) + 10 (called portion of SB/raise) = 20 to seat 0
    # seat 0 stack: 200 - 40 + 30 refund + 20 pot = 210
    # seat 1 stack: 200 - 10 = 190
    assert table.stacks_now() == (210, 190)
