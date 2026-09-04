"""ASCII playing-card faces for the terminal table."""

from __future__ import annotations

from collections.abc import Sequence

from rich.table import Table
from rich.text import Text

from holdem.domain.cards import Card, Rank, Suit

_RANK_LABELS = {
    Rank.TEN: "10",
    Rank.JACK: "J",
    Rank.QUEEN: "Q",
    Rank.KING: "K",
    Rank.ACE: "A",
}
_SUIT_STYLE = {
    Suit.HEARTS: ("♥", "red"),
    Suit.DIAMONDS: ("♦", "red"),
    Suit.CLUBS: ("♣", "green"),
    Suit.SPADES: ("♠", "white"),
}

CARD_HEIGHT = 5
CARD_WIDTH = 8
BOARD_SLOTS = 5
HOLE_SLOTS = 2


def rank_label(rank: Rank) -> str:
    """Human-readable rank: ``10`` for tens, face letters otherwise."""

    return _RANK_LABELS.get(rank, str(rank.value))


def suit_glyph(suit: Suit) -> tuple[str, str]:
    return _SUIT_STYLE[suit]


def card_text(card: Card) -> Text:
    """Compact coloured label such as ``10♥``."""

    glyph, colour = suit_glyph(card.suit)
    return Text(f"{rank_label(card.rank)}{glyph}", style=f"bold {colour}")


def cards_text(cards: Sequence[Card], *, empty: str = "—") -> Text:
    if not cards:
        return Text(empty, style="dim")
    result = Text()
    for index, card in enumerate(cards):
        if index:
            result.append(" ")
        result.append_text(card_text(card))
    return result


def card_face(card: Card | None) -> list[Text]:
    """Five-line mini playing card. ``None`` is an undealt placeholder."""

    if card is None:
        return [
            Text("╭──────╮", style="dim"),
            Text("│      │", style="dim"),
            Text("│  ·   │", style="dim"),
            Text("│      │", style="dim"),
            Text("╰──────╯", style="dim"),
        ]

    glyph, colour = suit_glyph(card.suit)
    rank = rank_label(card.rank)
    left = f"{rank:<2}"
    right = f"{rank:>2}"
    style = f"bold {colour}"
    return [
        Text("╭──────╮", style=colour),
        Text(f"│ {left}   │", style=style),
        Text(f"│  {glyph}   │", style=style),
        Text(f"│   {right} │", style=style),
        Text("╰──────╯", style=colour),
    ]


def cards_row(cards: Sequence[Card | None]) -> Text:
    """Place card faces side by side as a single block of text."""

    faces = [card_face(card) for card in cards]
    block = Text()
    for line in range(CARD_HEIGHT):
        if line:
            block.append("\n")
        for index, face in enumerate(faces):
            if index:
                block.append(" ")
            block.append_text(face[line])
    return block


def cards_grid(cards: Sequence[Card | None]) -> Table:
    """Card faces in a non-wrapping row, safe inside Rich panels."""

    grid = Table.grid(padding=(0, 1))
    for _ in cards:
        grid.add_column(no_wrap=True, justify="center")
    faces = [Text("\n").join(card_face(card)) for card in cards]
    grid.add_row(*faces)
    return grid


def board_row(board: Sequence[Card]) -> Table:
    """Always five community slots; undealt streets stay face-down."""

    slots: list[Card | None] = list(board)
    while len(slots) < BOARD_SLOTS:
        slots.append(None)
    return cards_grid(slots[:BOARD_SLOTS])


def hole_row(hole: Sequence[Card]) -> Table:
    """Two hole-card slots; empty before the deal."""

    slots: list[Card | None] = list(hole)
    while len(slots) < HOLE_SLOTS:
        slots.append(None)
    return cards_grid(slots[:HOLE_SLOTS])
