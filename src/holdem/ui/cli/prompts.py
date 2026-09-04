"""Validated terminal prompts for local play."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from rich.console import Console

from holdem.actors import BotDifficulty
from holdem.domain.actions import Action, ActionKind
from holdem.domain.views import LegalAction, SeatView

LineReader = Callable[[str], str]

DEFAULT_PLAYERS = 6
DEFAULT_STARTING_STACK = 1000
DEFAULT_SMALL_BLIND = 5
DEFAULT_BIG_BLIND = 10
DEFAULT_DISPLAY_NAME = "You"
MAX_DISPLAY_NAME_LENGTH = 24


@dataclass(frozen=True)
class PlayConfig:
    """Settings used to create a local or hosted table."""

    players: int = DEFAULT_PLAYERS
    starting_stack: int = DEFAULT_STARTING_STACK
    small_blind: int = DEFAULT_SMALL_BLIND
    big_blind: int = DEFAULT_BIG_BLIND
    seed: int | None = None
    bots: int = 0
    difficulty: BotDifficulty = BotDifficulty.MEDIUM

    def __post_init__(self) -> None:
        if not 2 <= self.players <= 9:
            raise ValueError("players must be between 2 and 9")
        if not 0 <= self.bots <= self.players - 1:
            raise ValueError("bots must be between 0 and players minus 1")
        if self.starting_stack <= 0:
            raise ValueError("starting stack must be positive")
        if self.small_blind <= 0 or self.big_blind <= 0:
            raise ValueError("blinds must be positive")
        if self.small_blind > self.big_blind:
            raise ValueError("small blind cannot exceed big blind")
        if self.starting_stack < self.big_blind:
            raise ValueError("starting stack must cover the big blind")

    @property
    def guest_slots(self) -> int:
        """Number of seats reserved for remote guests at a hosted table."""

        return self.players - 1 - self.bots

    def summary(self) -> str:
        return self._format_summary(self.bots)

    def local_summary(self) -> str:
        """Summary for a local table, where every other seat is a bot."""

        return self._format_summary(self.players - 1)

    def _format_summary(self, bots: int) -> str:
        return (
            f"{self.players} seats · {bots} bots ({self.difficulty.value}) · "
            f"{self.starting_stack} chips · "
            f"blinds {self.small_blind}/{self.big_blind}"
        )

    @classmethod
    def from_options(
        cls,
        *,
        players: int | None = None,
        starting_stack: int | None = None,
        blinds: tuple[int, int] | None = None,
        seed: int | None = None,
        bots: int | None = None,
        difficulty: BotDifficulty | str | None = None,
    ) -> PlayConfig:
        """Build a config, filling unspecified fields with cash-game defaults."""

        small, big = blinds if blinds is not None else (DEFAULT_SMALL_BLIND, DEFAULT_BIG_BLIND)
        return cls(
            players=DEFAULT_PLAYERS if players is None else players,
            starting_stack=DEFAULT_STARTING_STACK if starting_stack is None else starting_stack,
            small_blind=small,
            big_blind=big,
            seed=seed,
            bots=0 if bots is None else bots,
            difficulty=BotDifficulty.MEDIUM if difficulty is None else BotDifficulty(difficulty),
        )


def parse_blinds(raw: str) -> tuple[int, int]:
    """Parse a `small/big` blinds string."""

    parts = raw.split("/")
    try:
        if len(parts) != 2:
            raise ValueError
        small, big = (int(part.strip()) for part in parts)
    except ValueError:
        raise ValueError("Use the format small/big, for example 5/10.") from None
    if small <= 0 or big <= 0 or small > big:
        raise ValueError("Blinds must be positive and small cannot exceed big.")
    return small, big


def _read_text(
    label: str,
    *,
    reader: LineReader,
    console: Console,
    default: str,
    maximum: int | None = None,
) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        raw = reader(f"{label}{suffix}: ").strip()
        value = raw if raw else default
        if not value:
            console.print("[red]Enter a name.[/red]")
            continue
        if maximum is not None and len(value) > maximum:
            console.print(f"[red]Keep it to {maximum} characters or fewer.[/red]")
            continue
        return value


def _read_yes_no(
    label: str,
    *,
    reader: LineReader,
    console: Console,
    default: bool,
) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        raw = reader(f"{label} [{hint}]: ").strip().lower()
        if raw == "":
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        console.print("[red]Enter y or n.[/red]")


def _read_int(
    label: str,
    *,
    minimum: int,
    maximum: int | None,
    reader: LineReader,
    console: Console,
    default: int | None = None,
) -> int:
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = reader(f"{label}{suffix}: ").strip()
        if raw == "" and default is not None:
            value = default
        else:
            try:
                value = int(raw)
            except ValueError:
                console.print("[red]Enter a whole number.[/red]")
                continue
        if value < minimum or (maximum is not None and value > maximum):
            bounds = f"{minimum}–{maximum}" if maximum is not None else f"at least {minimum}"
            console.print(f"[red]Enter a value in the range {bounds}.[/red]")
            continue
        return value


def _read_blinds(
    *,
    reader: LineReader,
    console: Console,
    default: tuple[int, int] = (DEFAULT_SMALL_BLIND, DEFAULT_BIG_BLIND),
) -> tuple[int, int]:
    shown = f"{default[0]}/{default[1]}"
    while True:
        raw = reader(f"Blinds (small/big) [{shown}]: ").strip()
        if raw == "":
            return default
        try:
            return parse_blinds(raw)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")


def _read_difficulty(
    *,
    reader: LineReader,
    console: Console,
    default: BotDifficulty = BotDifficulty.MEDIUM,
) -> BotDifficulty:
    choices = "/".join(difficulty.value for difficulty in BotDifficulty)
    while True:
        raw = reader(f"Bot difficulty [{default.value}]: ").strip().lower()
        try:
            return default if not raw else BotDifficulty(raw)
        except ValueError:
            console.print(f"[red]Choose one of: {choices}.[/red]")


def prompt_play_config(
    *,
    reader: LineReader = input,
    console: Console | None = None,
    seed: int | None = None,
    players: int | None = None,
    starting_stack: int | None = None,
    blinds: tuple[int, int] | None = None,
    bots: int | None = None,
    difficulty: BotDifficulty | str | None = None,
    include_bots: bool = True,
) -> PlayConfig:
    """Prompt for a table configuration, accepting Enter for defaults."""

    output = console or Console()
    output.print("[bold]Table settings[/bold]")
    output.print("Press Enter to accept the default shown in brackets.")

    player_default = DEFAULT_PLAYERS if players is None else players
    stack_default = DEFAULT_STARTING_STACK if starting_stack is None else starting_stack
    blind_default = blinds if blinds is not None else (DEFAULT_SMALL_BLIND, DEFAULT_BIG_BLIND)
    bot_default = 0 if bots is None else bots
    difficulty_default = BotDifficulty.MEDIUM if difficulty is None else BotDifficulty(difficulty)

    seats = _read_int(
        "Players (including you)",
        minimum=2,
        maximum=9,
        reader=reader,
        console=output,
        default=player_default,
    )
    bot_count = min(bot_default, seats - 1)
    if include_bots:
        bot_count = _read_int(
            "Bots (hosted tables)",
            minimum=0,
            maximum=seats - 1,
            reader=reader,
            console=output,
            default=bot_count,
        )
    bot_difficulty = _read_difficulty(
        reader=reader,
        console=output,
        default=difficulty_default,
    )
    while True:
        stack = _read_int(
            "Starting stack",
            minimum=1,
            maximum=None,
            reader=reader,
            console=output,
            default=stack_default,
        )
        small, big = _read_blinds(reader=reader, console=output, default=blind_default)
        try:
            return PlayConfig(
                players=seats,
                starting_stack=stack,
                small_blind=small,
                big_blind=big,
                seed=seed,
                bots=bot_count,
                difficulty=bot_difficulty,
            )
        except ValueError as exc:
            output.print(f"[red]{exc}[/red] Choose a larger stack or smaller blinds.")


NEXT_HAND_PROMPT = "Press Enter for the next hand: "


def prompt_next_hand(*, reader: LineReader = input) -> None:
    """Hold the hand-over screen until the player is ready to continue."""

    reader(NEXT_HAND_PROMPT)


def prompt_bust_choice(
    *,
    reader: LineReader = input,
    console: Console | None = None,
) -> str:
    """Ask a busted player to leave or keep watching. Enter leaves."""

    output = console or Console()
    output.print()
    output.print("[bold red]You're out of chips.[/bold red]")
    output.print("  [cyan]1[/cyan]. Leave the table")
    output.print("  [cyan]2[/cyan]. Spectate the rest of the game")
    while True:
        raw = reader("Choose [1]: ").strip().lower()
        if raw in {"", "1", "l", "leave"}:
            return "leave"
        if raw in {"2", "s", "spectate"}:
            return "spectate"
        output.print("[red]Choose 1 to leave or 2 to spectate.[/red]")


class RichActionSource:
    """Show only engine-approved actions and collect one valid choice."""

    def __init__(
        self,
        *,
        console: Console | None = None,
        reader: LineReader = input,
    ) -> None:
        self.console = console or Console()
        self.reader = reader

    def __call__(self, view: SeatView) -> Action:
        if not view.legal_actions:
            raise ValueError(f"seat {view.seat_id} has no legal actions")

        choices = {str(index): legal for index, legal in enumerate(view.legal_actions, start=1)}
        self.console.print("[bold]Your action[/bold]")
        for key, legal in choices.items():
            self.console.print(f"  [cyan]{key}[/cyan]. {self._label(legal, view)}")

        while True:
            selected = choices.get(self.reader("Choose action: ").strip())
            if selected is None:
                self.console.print("[red]Choose one of the listed numbers.[/red]")
                continue
            return self._materialize(selected)

    def _materialize(self, legal: LegalAction) -> Action:
        if legal.kind == ActionKind.FOLD:
            return Action.fold()
        if legal.kind == ActionKind.CHECK:
            return Action.check()
        if legal.kind == ActionKind.CALL:
            return Action.call()
        if legal.kind == ActionKind.ALL_IN:
            return Action.all_in()
        if legal.kind != ActionKind.RAISE:
            raise ValueError(f"unsupported action {legal.kind.value}")
        if legal.min_amount is None or legal.max_amount is None:
            raise ValueError("raise action is missing its bounds")

        amount = _read_int(
            f"Raise to ({legal.min_amount}–{legal.max_amount})",
            minimum=legal.min_amount,
            maximum=legal.max_amount,
            reader=self.reader,
            console=self.console,
        )
        return Action.raise_to(amount)

    @staticmethod
    def _label(legal: LegalAction, view: SeatView) -> str:
        if legal.kind == ActionKind.CALL:
            seat = next(seat for seat in view.seats if seat.seat_id == view.seat_id)
            return f"Call {max(0, view.current_bet - seat.street_bet)}"
        if legal.kind == ActionKind.RAISE:
            return f"Raise to {legal.min_amount}–{legal.max_amount}"
        if legal.kind == ActionKind.ALL_IN:
            seat = next(seat for seat in view.seats if seat.seat_id == view.seat_id)
            return f"All in ({seat.stack})"
        return str(legal.kind.value).replace("_", " ").title()
