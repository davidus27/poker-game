"""ASCII card faces and compact labels."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from holdem.domain.cards import Rank, parse_card
from holdem.ui.cli.card_art import board_row, card_face, card_text, hole_row, rank_label


def _plain(renderable: object) -> str:
    stream = StringIO()
    Console(file=stream, force_terminal=False, width=80).print(renderable)
    return stream.getvalue()


def test_ten_is_shown_as_10_not_t() -> None:
    ten = parse_card("Th")
    assert rank_label(Rank.TEN) == "10"
    assert card_text(ten).plain == "10♥"
    assert "T♥" not in card_text(ten).plain
    face = "\n".join(line.plain for line in card_face(ten))
    assert "10" in face
    assert "T" not in face.replace("10", "")


def test_empty_board_has_five_placeholder_slots() -> None:
    row = _plain(board_row(()))
    assert row.count("·") == 5
    assert row.count("╭") == 5


def test_dealt_board_fills_slots_from_the_left() -> None:
    flop = (parse_card("Ah"), parse_card("Kd"), parse_card("2c"))
    row = _plain(board_row(flop))
    assert "A" in row
    assert "K" in row
    assert "2" in row
    assert row.count("·") == 2


def test_hole_row_shows_two_card_faces() -> None:
    hole = (parse_card("Qs"), parse_card("Jh"))
    row = _plain(hole_row(hole))
    assert row.count("╭") == 2
    assert "Q" in row
    assert "J" in row
    assert "♠" in row
    assert "♥" in row
