"""Rich CLI rendering and prompt behavior."""

from __future__ import annotations

from dataclasses import replace
from io import StringIO

import pytest
from rich.console import Console

from holdem.actors import BotDifficulty
from holdem.domain import (
    Action,
    ActionKind,
    ActionRequested,
    HandStarted,
    HoleDealt,
    LegalAction,
    PlayerActed,
    PotAward,
    PotsAwarded,
    PotView,
    PublicSeat,
    SeatStatus,
    SeatView,
    Showdown,
    ShowdownHand,
    Street,
    TournamentEnded,
    parse_cards,
)
from holdem.domain.hands import find_best_hand
from holdem.ui.cli import (
    PlayConfig,
    RichActionSource,
    RichView,
    prompt_bust_choice,
    prompt_play_config,
)
from holdem.ui.cli.brand import LOGO_TITLE
from holdem.ui.cli.interact import Cancelled


def _console() -> tuple[Console, StringIO]:
    stream = StringIO()
    return Console(file=stream, force_terminal=False, width=100), stream


def _view(*legal: LegalAction) -> SeatView:
    seats = (
        PublicSeat(0, 90, SeatStatus.ACTIVE, 10, 10),
        PublicSeat(1, 80, SeatStatus.ACTIVE, 20, 20),
    )
    return SeatView(
        seat_id=0,
        street=Street.FLOP,
        hand_number=2,
        button=1,
        small_blind=5,
        big_blind=10,
        board=parse_cards("Ah Kd 2c"),
        hole=parse_cards("Qs Js"),
        pot_total=30,
        pots=(PotView(30, frozenset({0, 1})),),
        seats=seats,
        to_act=0,
        legal_actions=legal,
        current_bet=20,
        min_raise_to=40,
    )


def test_renderer_shows_table_private_cards_and_latest_action() -> None:
    console, stream = _console()
    renderer = RichView(console=console, clear_screen=False)
    events = [
        HoleDealt(1, parse_cards("Ac Ad")),
        PlayerActed(1, Action.raise_to(20), chips=10, stack=80, street_bet=20),
    ]

    renderer.render(events, _view())
    output = stream.getvalue()

    assert LOGO_TITLE in output
    assert "Hand 2" in output
    assert "Flop" in output
    assert "A" in output and "♥" in output
    assert "K" in output and "♦" in output
    assert "Q" in output and "♠" in output
    assert "J" in output
    assert "Bot 1 raises to 20." in output
    assert "A♣" not in output
    assert "30" in output
    assert "You" in output
    assert "╭" in output
    assert "The felt" in output
    assert "Your hand" in output
    assert "Last" in output


def test_renderer_uses_display_name_for_the_local_seat() -> None:
    console, stream = _console()
    renderer = RichView(console=console, clear_screen=False, display_name="Dave")

    renderer.render([], _view())

    assert "Dave" in stream.getvalue()


def test_renderer_uses_online_names_for_other_seats() -> None:
    console, stream = _console()
    renderer = RichView(
        console=console,
        clear_screen=False,
        display_name="Dave",
        seat_names={1: "Ava"},
    )

    renderer.render([], _view())

    assert "Ava" in stream.getvalue()


def test_renderer_uses_playing_card_faces_and_keeps_the_last_bot_action() -> None:
    console, stream = _console()
    renderer = RichView(console=console, clear_screen=False)
    ten_view = replace(_view(), hole=parse_cards("Th 5c"), board=(), street=Street.PREFLOP)

    renderer.render(
        [PlayerActed(1, Action.raise_to(20), chips=10, stack=80, street_bet=20)],
        ten_view,
    )
    renderer.render([], ten_view, thinking_seat=1)
    output = stream.getvalue()

    assert "10" in output
    assert "T♥" not in output
    assert "thinking…" in output
    assert "raises to 20" in output


def test_showdown_names_each_made_hand() -> None:
    console, stream = _console()
    renderer = RichView(console=console, clear_screen=False)
    board = parse_cards("3h 2d 8c 5d Qd")
    you = parse_cards("2h Th")
    bot = parse_cards("Jh 4h")
    events = [
        Showdown(
            revelations=(
                ShowdownHand(0, (you[0], you[1]), find_best_hand(list(board), list(you))),
                ShowdownHand(1, (bot[0], bot[1]), find_best_hand(list(board), list(bot))),
            )
        ),
        PotsAwarded((PotAward(0, 4_220, (0,), (4_220,)),)),
    ]

    renderer.render(events, replace(_view(), board=board, hole=you, street=Street.HAND_OVER))
    output = stream.getvalue()

    assert "Showdown" in output
    assert "You win 4,220." in output
    assert "one pair" in output
    assert "high card" in output
    assert "You — one pair" in output
    assert "Bot 1 — high card" in output
    assert "Your hand" not in output


def test_fold_win_shows_a_winner_panel_and_holds_the_board() -> None:
    console, stream = _console()
    renderer = RichView(console=console, clear_screen=False, display_name="Dave")
    view = replace(
        _view(),
        street=Street.HAND_OVER,
        hand_number=3,
        board=(),
        hole=parse_cards("Ah Jh"),
        to_act=None,
        legal_actions=(),
        pot_total=20,
        pots=(PotView(20, frozenset({0})),),
        seats=(
            PublicSeat(0, 1_216, SeatStatus.ALL_IN, 1_206, 1_206),
            PublicSeat(1, 784, SeatStatus.FOLDED, 10, 10),
        ),
    )

    renderer.render(
        [PotsAwarded((PotAward(0, 20, (0,), (20,)),))],
        view,
    )
    output = stream.getvalue()

    assert "Winner" in output
    assert "Dave wins 20." in output
    assert "Bot 1 folded." in output
    assert "folded before the flop" in output
    assert "Hand over" in output
    assert "Showdown" not in output
    assert "waiting for the flop" not in output


def test_next_hand_clears_the_result_panel() -> None:
    console, stream = _console()
    renderer = RichView(console=console, clear_screen=False)
    board = parse_cards("3h 2d 8c 5d Qd")
    you = parse_cards("2h Th")
    bot = parse_cards("Jh 4h")
    renderer.render(
        [
            Showdown(
                revelations=(
                    ShowdownHand(0, (you[0], you[1]), find_best_hand(list(board), list(you))),
                    ShowdownHand(1, (bot[0], bot[1]), find_best_hand(list(board), list(bot))),
                )
            ),
            PotsAwarded((PotAward(0, 4_220, (0,), (4_220,)),)),
        ],
        replace(_view(), board=board, hole=you, street=Street.HAND_OVER),
    )
    start = stream.tell()
    renderer.render(
        [HandStarted(4, 1, (90, 80))],
        replace(_view(), street=Street.PREFLOP, hand_number=4, board=(), hole=parse_cards("4c Jh")),
    )
    later = stream.getvalue()[start:]

    assert "You win 4,220." not in later
    assert "Showdown" not in later
    assert "Hand 4" in later
    assert "Preflop" in later


def test_local_player_actions_use_first_person() -> None:
    console, stream = _console()
    renderer = RichView(console=console, clear_screen=False)
    renderer.render(
        [PlayerActed(0, Action.call(), chips=10, stack=90, street_bet=20)],
        _view(),
    )
    output = stream.getvalue()
    assert "You call 10." in output
    assert "You calls" not in output


def test_named_local_player_uses_third_person_grammar() -> None:
    console, stream = _console()
    renderer = RichView(console=console, clear_screen=False, display_name="Dave")
    renderer.render(
        [
            PlayerActed(0, Action.call(), chips=10, stack=90, street_bet=20),
            TournamentEnded(0),
        ],
        _view(),
    )

    output = stream.getvalue()
    assert "Dave calls 10." in output
    assert "Dave wins the game!" in output


def test_renderer_identifies_the_player_whose_turn_is_pending() -> None:
    console, stream = _console()
    renderer = RichView(
        console=console,
        clear_screen=False,
        seat_names={1: "Ava"},
    )

    renderer.render([ActionRequested(1)], _view())

    assert "Waiting for Ava to act…" in stream.getvalue()


def test_spectating_hides_hole_cards() -> None:
    console, stream = _console()
    renderer = RichView(console=console, clear_screen=False)
    renderer.render([], _view(), spectating=True)
    output = stream.getvalue()
    assert "Spectating — you are out" in output
    assert "Your hand" not in output


def test_bust_prompt_defaults_to_leave() -> None:
    console, stream = _console()

    assert prompt_bust_choice(reader=lambda _prompt: "", console=console) == "leave"
    assert prompt_bust_choice(reader=lambda _prompt: "2", console=console) == "spectate"
    assert "You're out of chips." in stream.getvalue()


def test_action_prompt_lists_only_legal_actions() -> None:
    console, stream = _console()
    responses = iter(["9", "2"])
    source = RichActionSource(console=console, reader=lambda _prompt: next(responses))
    view = _view(
        LegalAction(ActionKind.CHECK),
        LegalAction(ActionKind.ALL_IN),
    )

    assert source(view) == Action.all_in()
    output = stream.getvalue()
    assert "Check" in output
    assert "All in (90)" in output
    assert "Fold" not in output
    assert "Call" not in output
    assert "Raise" not in output
    assert "Choose one of the listed numbers." in output


def test_ctrl_c_at_action_prompt_cancels_the_table() -> None:
    console, _stream = _console()

    def interrupt(_prompt: str) -> str:
        raise KeyboardInterrupt

    source = RichActionSource(console=console, reader=interrupt)

    with pytest.raises(Cancelled):
        source(_view(LegalAction(ActionKind.CHECK)))


def test_raise_prompt_retries_until_amount_is_in_legal_range() -> None:
    console, stream = _console()
    responses = iter(["1", "39", "101", "75"])
    source = RichActionSource(console=console, reader=lambda _prompt: next(responses))

    action = source(_view(LegalAction(ActionKind.RAISE, min_amount=40, max_amount=100)))

    assert action == Action.raise_to(75)
    assert stream.getvalue().count("Enter a value in the range 40–100.") == 2


def test_setup_prompt_accepts_empty_input_as_defaults() -> None:
    console, stream = _console()
    prompts: list[str] = []

    def reader(prompt: str) -> str:
        prompts.append(prompt)
        return ""

    config = prompt_play_config(reader=reader, console=console, seed=42)

    assert config == PlayConfig(seed=42)
    assert prompts == [
        "Players (including you) [6]: ",
        "Bots (hosted tables) [0]: ",
        "Bot difficulty [medium]: ",
        "Starting stack [1000]: ",
        "Blinds (small/big) [5/10]: ",
    ]
    assert "Press Enter to accept the default shown in brackets." in stream.getvalue()


def test_setup_prompt_validates_each_value() -> None:
    console, stream = _console()
    responses = iter(
        [
            "one",
            "1",
            "3",
            "-1",
            "3",
            "1",
            "expert",
            "hard",
            "0",
            "100",
            "10",
            "10/5",
            "5/200",
            "50",
            "5/10",
        ]
    )

    config = prompt_play_config(
        reader=lambda _prompt: next(responses),
        console=console,
        seed=42,
    )

    assert config == PlayConfig(
        3,
        50,
        5,
        10,
        seed=42,
        bots=1,
        difficulty=BotDifficulty.HARD,
    )
    output = stream.getvalue()
    assert "Enter a whole number." in output
    assert "Enter a value in the range 2–9." in output
    assert "Enter a value in the range 0–2." in output
    assert "Choose one of: easy/medium/hard." in output
    assert "Use the format small/big" in output
    assert "small cannot exceed big" in output
    assert "starting stack must cover the big blind" in output
    assert "Choose a larger stack or smaller blinds." in output


def test_play_config_reports_hosted_bot_seats() -> None:
    config = PlayConfig(players=6, bots=2, difficulty=BotDifficulty.HARD)

    assert config.guest_slots == 3
    assert config.summary() == "6 seats · 2 bots (hard) · 1000 chips · blinds 5/10"
    assert config.local_summary() == "6 seats · 5 bots (hard) · 1000 chips · blinds 5/10"


def test_setup_prompt_can_skip_hosted_bot_count() -> None:
    console, _stream = _console()
    prompts: list[str] = []

    def reader(prompt: str) -> str:
        prompts.append(prompt)
        return "hard" if prompt.startswith("Bot difficulty") else ""

    config = prompt_play_config(
        reader=reader,
        console=console,
        include_bots=False,
        bots=2,
    )

    assert config == PlayConfig(bots=2, difficulty=BotDifficulty.HARD)
    assert prompts == [
        "Players (including you) [6]: ",
        "Bot difficulty [medium]: ",
        "Starting stack [1000]: ",
        "Blinds (small/big) [5/10]: ",
    ]
