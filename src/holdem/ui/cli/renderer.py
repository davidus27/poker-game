"""Rich renderer for seat-private table snapshots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from holdem.domain.actions import ActionKind
from holdem.domain.cards import Card, HandRank, HandScore
from holdem.domain.events import (
    ActionRequested,
    BlindPosted,
    Event,
    HandStarted,
    HoleDealt,
    PlayerActed,
    PlayerBusted,
    PotsAwarded,
    Showdown,
    StreetDealt,
    TournamentEnded,
)
from holdem.domain.views import SeatStatus, SeatView, Street
from holdem.ui.cli.brand import logo_mark
from holdem.ui.cli.card_art import board_row, cards_text, hole_row

_HAND_NAMES = {
    HandRank.HIGH_CARD: "high card",
    HandRank.PAIR: "one pair",
    HandRank.TWO_PAIR: "two pair",
    HandRank.THREE_OF_A_KIND: "three of a kind",
    HandRank.STRAIGHT: "a straight",
    HandRank.FLUSH: "a flush",
    HandRank.FULL_HOUSE: "a full house",
    HandRank.FOUR_OF_A_KIND: "four of a kind",
    HandRank.STRAIGHT_FLUSH: "a straight flush",
    HandRank.ROYAL_FLUSH: "a royal flush",
}
_LOG_LIMIT = 8
_STREET_TITLES = {
    Street.WAITING: "Waiting",
    Street.PREFLOP: "Preflop",
    Street.FLOP: "Flop",
    Street.TURN: "Turn",
    Street.RIVER: "River",
    Street.SHOWDOWN: "Showdown",
    Street.HAND_OVER: "Hand over",
    Street.TOURNAMENT_OVER: "Tournament over",
}


class RichView:
    """Render the table, private cards, and latest public events."""

    def __init__(
        self,
        *,
        console: Console | None = None,
        clear_screen: bool = True,
        display_name: str = "You",
        seat_names: Mapping[int, str] | None = None,
    ) -> None:
        self.console = console or Console()
        self.clear_screen = clear_screen
        self.display_name = display_name
        self.seat_names = dict(seat_names or {})
        self._headline: str | None = None
        self._log: list[str] = []
        self._seat_last: dict[int, str] = {}
        self._showdown: Showdown | None = None
        self._awards: PotsAwarded | None = None
        self._tournament: TournamentEnded | None = None

    def render(
        self,
        events: Sequence[Event],
        view: SeatView,
        *,
        thinking_seat: int | None = None,
        spectating: bool = False,
    ) -> None:
        self._ingest(events, view.seat_id)
        if thinking_seat is not None:
            who = self._who(thinking_seat, view.seat_id)
            self._headline = f"{who} is thinking…"
        if self.clear_screen:
            self.console.clear()
        self.console.print(self._layout(view, thinking_seat=thinking_seat, spectating=spectating))

    def _layout(
        self,
        view: SeatView,
        *,
        thinking_seat: int | None,
        spectating: bool = False,
    ) -> RenderableType:
        seats = Table(expand=True, box=None, show_header=True, pad_edge=False)
        seats.add_column("Seat", style="bold")
        seats.add_column("Stack", justify="right")
        seats.add_column("Bet", justify="right")
        seats.add_column("Status")
        seats.add_column("Last")

        for seat in view.seats:
            markers: list[str] = []
            if seat.seat_id == view.button:
                markers.append("D")
            if seat.seat_id == view.to_act:
                markers.append("→")
            name = self._who(seat.seat_id, view.seat_id)
            label = f"{escape(name)} {' '.join(markers)}".rstrip()
            status_style = {
                SeatStatus.ACTIVE: "green",
                SeatStatus.ALL_IN: "yellow",
                SeatStatus.FOLDED: "dim",
                SeatStatus.BUSTED: "red",
            }[seat.status]
            last_cell: str | Text
            if thinking_seat == seat.seat_id:
                last_cell = Text("thinking…", style="italic cyan")
            else:
                last_cell = self._seat_last.get(seat.seat_id, "—")
            seats.add_row(
                label,
                f"{seat.stack:,}",
                f"{seat.street_bet:,}",
                Text(seat.status.value.replace("_", " ").title(), style=status_style),
                last_cell,
            )

        felt = Table.grid(expand=True, padding=(0, 0))
        felt.add_column(justify="center")
        felt.add_row(Text(self._board_caption(view), style="bold"))
        felt.add_row(Align.center(board_row(view.board)))
        felt.add_row(Text(f"Pot {self._pot_label(view)}", style="bold yellow"))
        felt.add_row(Text(""))
        if spectating:
            felt.add_row(Text("Spectating — you are out", style="bold dim"))
        elif self._showdown is None:
            felt.add_row(Text("Your hand", style="bold"))
            felt.add_row(Align.center(hole_row(view.hole)))

        if view.street is Street.TOURNAMENT_OVER:
            street = _STREET_TITLES[Street.TOURNAMENT_OVER]
        elif self._showdown is not None:
            street = _STREET_TITLES[Street.SHOWDOWN]
        else:
            street = _STREET_TITLES.get(view.street, view.street.value)
        settled = self._has_result()
        headline = self._headline or "Waiting for action…"
        history = self._log[-_LOG_LIMIT:]
        if history and history[-1] == headline:
            history = history[:-1]
        latest = Text()
        latest.append(headline, style="bold yellow")
        if history:
            latest.append("\n")
            latest.append("\n".join(history), style="dim")

        sections: list[RenderableType] = [
            Align.center(logo_mark()),
            Text(
                f"Hand {view.hand_number}  ·  {street}",
                style="bold gold1" if settled else "bold",
                justify="center",
            ),
            Panel(felt, title="The felt", border_style="blue"),
        ]
        result = self._result_panel(view)
        if result is not None:
            sections.append(result)
        sections.append(Panel(seats, title="Table", border_style="cyan"))
        sections.append(Panel(latest, title="Latest", border_style="magenta"))
        return Group(*sections)

    def _ingest(self, events: Sequence[Event], viewer: int) -> None:
        for event in events:
            if isinstance(event, HandStarted):
                self._seat_last.clear()
                self._log.clear()
                self._showdown = None
                self._awards = None
                self._tournament = None
                line = f"Hand {event.hand_number} dealt."
                self._push(line)
            elif isinstance(event, BlindPosted):
                who = self._who(event.seat_id, viewer)
                kind = event.kind.value
                verb = "post" if who == "You" else "posts"
                line = f"{who} {verb} the {kind} blind ({event.amount:,})."
                self._seat_last[event.seat_id] = f"posts {kind} {event.amount:,}"
                self._push(line)
            elif isinstance(event, HoleDealt):
                if event.seat_id == viewer:
                    self._push("Your hole cards were dealt.")
            elif isinstance(event, ActionRequested):
                who = self._who(event.seat_id, viewer)
                self._headline = (
                    "Your turn." if event.seat_id == viewer else f"Waiting for {who} to act…"
                )
            elif isinstance(event, PlayerActed):
                line = self._action_line(event, viewer)
                self._seat_last[event.seat_id] = self._action_short(event)
                self._push(line)
            elif isinstance(event, StreetDealt):
                street = _STREET_TITLES.get(event.street, event.street.value)
                line = f"{street} dealt: {cards_text(event.cards).plain}"
                self._push(line)
            elif isinstance(event, Showdown):
                self._showdown = event
            elif isinstance(event, PotsAwarded):
                self._awards = event
            elif isinstance(event, PlayerBusted):
                self._push(f"{self._who(event.seat_id, viewer)} busted.")
            elif isinstance(event, TournamentEnded):
                self._tournament = event
                who = self._who(event.winner, viewer)
                verb = "win" if who == "You" else "wins"
                self._push(f"{who} {verb} the game!")

    def _push(self, line: str) -> None:
        self._headline = line
        self._log.append(line)
        if len(self._log) > _LOG_LIMIT * 2:
            self._log = self._log[-_LOG_LIMIT:]

    def _who(self, seat_id: int, viewer: int) -> str:
        if seat_id == viewer:
            return self.display_name
        return self.seat_names.get(seat_id, f"Bot {seat_id}")

    def _has_result(self) -> bool:
        return self._showdown is not None or self._awards is not None

    def _result_panel(self, view: SeatView) -> Panel | None:
        if not self._has_result():
            return None

        body = Table.grid(expand=True, padding=(0, 0))
        body.add_column(justify="center")
        for line in self._verdict_lines(view.seat_id):
            body.add_row(Text(line, style="bold gold1"))
        if self._showdown is not None:
            body.add_row(Text(""))
            body.add_row(self._showdown_hands(view.seat_id))
        else:
            folded = self._folded_line(view)
            if folded is not None:
                body.add_row(Text(folded, style="dim italic"))

        title = "Showdown" if self._showdown is not None else "Winner"
        return Panel(body, title=title, border_style="gold1")

    def _showdown_hands(self, viewer: int) -> Table:
        assert self._showdown is not None
        revelations = self._showdown.revelations
        winners = self._winner_seats()
        hands = Table(expand=True, box=None, show_header=False, pad_edge=False)
        for _ in revelations:
            hands.add_column(justify="center", ratio=1)

        names: list[Text] = []
        cards: list[Align] = []
        made: list[Text] = []
        for hand in revelations:
            who = self._who(hand.seat_id, viewer)
            won = hand.seat_id in winners
            style = "bold green" if won else "bold dim"
            label = f"{who}  ★" if won else who
            names.append(Text(label, style=style, justify="center"))
            cards.append(Align.center(hole_row(hand.hole)))
            made.append(
                Text(
                    f"{who} — {describe_hand(hand.score)}",
                    style="green" if won else "dim",
                    justify="center",
                )
            )
        hands.add_row(*names)
        hands.add_row(*cards)
        hands.add_row(*made)
        return hands

    def _verdict_lines(self, viewer: int) -> list[str]:
        lines: list[str] = []
        if self._awards is not None:
            lines.append(self._awards_summary(self._awards, viewer))
        if self._tournament is not None:
            who = self._who(self._tournament.winner, viewer)
            verb = "win" if who == "You" else "wins"
            lines.append(f"{who} {verb} the game!")
        return lines

    def _awards_summary(self, awarded: PotsAwarded, viewer: int) -> str:
        if not awarded.awards:
            return "No pot awarded."
        if len(awarded.awards) == 1:
            award = awarded.awards[0]
            return self._pot_won_line(award.winners, award.amount, viewer)
        parts = []
        for index, award in enumerate(awarded.awards):
            label = "Main pot" if index == 0 else f"Side pot {index}"
            names = _join_names([self._who(seat, viewer) for seat in award.winners])
            parts.append(f"{label} {award.amount:,} to {names}")
        return ". ".join(parts) + "."

    def _pot_won_line(self, winners: tuple[int, ...], amount: int, viewer: int) -> str:
        names = [self._who(seat, viewer) for seat in winners]
        if len(names) == 1:
            who = names[0]
            verb = "win" if who == "You" else "wins"
            return f"{who} {verb} {amount:,}."
        return f"{_join_names(names)} split {amount:,}."

    def _winner_seats(self) -> frozenset[int]:
        if self._awards is None:
            return frozenset()
        winners: set[int] = set()
        for award in self._awards.awards:
            winners.update(award.winners)
        return frozenset(winners)

    def _folded_line(self, view: SeatView) -> str | None:
        folded = [
            self._who(seat.seat_id, view.seat_id)
            for seat in view.seats
            if seat.status is SeatStatus.FOLDED
        ]
        if not folded:
            return None
        if len(folded) == 1:
            return f"{folded[0]} folded."
        return f"{_join_names(folded)} folded."

    @staticmethod
    def _board_caption(view: SeatView) -> str:
        dealt = len(view.board)
        if dealt == 0:
            if view.street in {Street.HAND_OVER, Street.TOURNAMENT_OVER, Street.SHOWDOWN}:
                return "Board  ·  folded before the flop"
            return "Board  ·  waiting for the flop"
        if dealt == 3:
            return "Board  ·  flop"
        if dealt == 4:
            return "Board  ·  turn"
        return "Board  ·  river"

    @staticmethod
    def _pot_label(view: SeatView) -> str:
        total = f"{view.pot_total:,}"
        if len(view.pots) <= 1:
            return total
        layers = " · ".join(f"{pot.amount:,}" for pot in view.pots)
        return f"{total}  ({layers})"

    def _action_line(self, event: PlayerActed, viewer: int) -> str:
        who = self._who(event.seat_id, viewer)
        return f"{who} {self._action_phrase(event, first_person=who == 'You')}."

    @staticmethod
    def _action_short(event: PlayerActed) -> str:
        return RichView._action_phrase(event, first_person=False)

    @staticmethod
    def _action_phrase(event: PlayerActed, *, first_person: bool) -> str:
        kind = event.action.kind
        if kind is ActionKind.FOLD:
            return "fold" if first_person else "folds"
        if kind is ActionKind.CHECK:
            return "check" if first_person else "checks"
        if kind is ActionKind.CALL:
            verb = "call" if first_person else "calls"
            return f"{verb} {event.chips:,}"
        if kind is ActionKind.RAISE:
            amount = event.action.amount if event.action.amount is not None else event.street_bet
            verb = "raise" if first_person else "raises"
            return f"{verb} to {amount:,}"
        verb = "go" if first_person else "goes"
        return f"{verb} all in ({event.street_bet:,})"


def _join_names(names: Sequence[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def describe_hand(score: HandScore) -> str:
    """Human-readable made hand, including the five cards that play."""

    name = _HAND_NAMES[score.rank]
    made = _made_cards(score)
    return f"{name} {cards_text(made).plain}"


def _made_cards(score: HandScore) -> tuple[Card, ...]:
    if score.rank is HandRank.HIGH_CARD:
        ordered = sorted(score.cards, key=lambda card: card.rank.value, reverse=True)
        return tuple(ordered[:5])
    return tuple(score.cards[:5])
