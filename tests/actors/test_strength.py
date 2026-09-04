"""Table-driven tests for pure poker strength estimates."""

from __future__ import annotations

import random

import pytest

from holdem.actors.strength import (
    DrawOuts,
    chen_score,
    chen_strength,
    count_draw_outs,
    draw_equity,
    monte_carlo_equity,
    pot_odds,
)
from holdem.domain import PublicSeat, SeatStatus, SeatView, Street, parse_cards


@pytest.mark.parametrize(
    ("cards", "expected"),
    [
        ("As Ah", 20.0),
        ("As Ks", 12.0),
        ("As Kh", 10.0),
        ("7s 2h", -1.5),
        ("5s 5h", 5.0),
        ("Js Ts", 9.0),
        ("9s 7s", 6.5),
    ],
)
def test_chen_score_known_starting_hands(cards: str, expected: float) -> None:
    assert chen_score(parse_cards(cards)) == expected


@pytest.mark.parametrize(
    ("cards", "expected"),
    [
        ("As Ah", 1.0),
        ("As Ks", 0.6),
        ("7s 2h", 0.0),
    ],
)
def test_chen_strength_is_normalized(cards: str, expected: float) -> None:
    assert chen_strength(parse_cards(cards)) == expected


@pytest.mark.parametrize(
    ("hole", "board", "expected"),
    [
        ("Ah Kh", "2h 7h Qc", DrawOuts(flush=9, straight=0, total=9)),
        ("8s 7d", "6c 5h Kc", DrawOuts(flush=0, straight=8, total=8)),
        ("Ah Kh", "2h 7h Qc 3s 4d", DrawOuts(flush=0, straight=0, total=0)),
        ("Ah Kd", "2c 7s Qh", DrawOuts(flush=0, straight=0, total=0)),
    ],
)
def test_count_draw_outs(
    hole: str,
    board: str,
    expected: DrawOuts,
) -> None:
    assert count_draw_outs(parse_cards(hole), parse_cards(board)) == expected


@pytest.mark.parametrize(
    ("hole", "board", "expected"),
    [
        ("Ah Kh", "2h 7h Qc", 0.36),
        ("8s 7d", "6c 5h Kc 2s", 0.16),
        ("8s 7d", "6c 5h Kc 2s 3d", 0.0),
    ],
)
def test_draw_equity_uses_rule_of_four_and_two(
    hole: str,
    board: str,
    expected: float,
) -> None:
    assert draw_equity(parse_cards(hole), parse_cards(board)) == expected


def _view(
    *,
    hole: str = "As Ah",
    board: str = "",
    hero_bet: int = 10,
    current_bet: int = 30,
    pot_total: int = 60,
    opponent_statuses: tuple[SeatStatus, ...] = (SeatStatus.ACTIVE,),
) -> SeatView:
    seats = [
        PublicSeat(
            seat_id=0,
            stack=100,
            status=SeatStatus.ACTIVE,
            street_bet=hero_bet,
            committed=hero_bet,
        )
    ]
    seats.extend(
        PublicSeat(
            seat_id=index,
            stack=100,
            status=status,
            street_bet=current_bet,
            committed=current_bet,
        )
        for index, status in enumerate(opponent_statuses, start=1)
    )
    return SeatView(
        seat_id=0,
        street=Street.RIVER if len(parse_cards(board)) == 5 else Street.PREFLOP,
        hand_number=1,
        button=1,
        small_blind=5,
        big_blind=10,
        board=parse_cards(board),
        hole=parse_cards(hole),
        pot_total=pot_total,
        pots=(),
        seats=tuple(seats),
        to_act=0,
        legal_actions=(),
        current_bet=current_bet,
        min_raise_to=None,
    )


@pytest.mark.parametrize(
    ("hero_bet", "current_bet", "pot_total", "expected"),
    [
        (10, 30, 60, 0.25),
        (30, 30, 60, 0.0),
        (40, 30, 60, 0.0),
    ],
)
def test_pot_odds(
    hero_bet: int,
    current_bet: int,
    pot_total: int,
    expected: float,
) -> None:
    view = _view(hero_bet=hero_bet, current_bet=current_bet, pot_total=pot_total)
    assert pot_odds(view) == expected


@pytest.mark.parametrize(
    ("hole", "board", "expected"),
    [
        ("Ts 2c", "As Ks Qs Js 3d", 1.0),
        ("2c 3d", "As Ks Qs Js Ts", 0.5),
    ],
)
def test_monte_carlo_equity_for_certain_river_results(
    hole: str,
    board: str,
    expected: float,
) -> None:
    assert monte_carlo_equity(_view(hole=hole, board=board), random.Random(7), samples=20) == expected


def test_monte_carlo_is_seeded_and_ignores_folded_seats() -> None:
    view = _view(
        hole="As Kd",
        board="Ah 7c 2s",
        opponent_statuses=(SeatStatus.ACTIVE, SeatStatus.FOLDED),
    )

    first = monte_carlo_equity(view, random.Random(42), samples=40)
    second = monte_carlo_equity(view, random.Random(42), samples=40)

    assert first == second
    assert 0.0 <= first <= 1.0
