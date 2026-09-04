"""Lobby intro, menu, and placeholder host/join flows."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from holdem.app.lobby import run_lobby
from holdem.app.online import GuestResult, HostResult
from holdem.ui.cli import MenuOption, PlayConfig


def _console() -> tuple[Console, StringIO]:
    stream = StringIO()
    return Console(file=stream, force_terminal=False, width=100), stream


def test_new_game_asks_before_using_defaults() -> None:
    console, stream = _console()
    responses = iter(["Dave", "1", "", "", "6"])
    prompts: list[str] = []
    played: list[tuple[PlayConfig, str]] = []

    def reader(prompt: str) -> str:
        prompts.append(prompt)
        return next(responses)

    def fake_play(
        config: PlayConfig,
        *,
        display_name: str,
        **_kwargs: object,
    ) -> int:
        played.append((config, display_name))
        return 0

    run_lobby(console=console, reader=reader, play=fake_play)

    assert played == [(PlayConfig(), "Dave")]
    assert prompts[0].startswith("What should we call you?")
    assert any(prompt.startswith("Change these settings?") for prompt in prompts)
    output = stream.getvalue()
    assert "TEXAS HOLD'EM" in output
    assert "Hi, Dave." in output
    assert "New local game" in output
    assert "You won!" in output
    assert "See you at the table." in output


def test_settings_persist_into_the_next_local_game() -> None:
    console, _stream = _console()
    responses = iter(["Ava", "4", "3", "", "", "1", "", "", "6"])
    played: list[PlayConfig] = []

    def fake_play(config: PlayConfig, **_kwargs: object) -> int:
        played.append(config)
        return 1

    run_lobby(
        console=console,
        reader=lambda _prompt: next(responses),
        play=fake_play,
    )

    assert played == [PlayConfig(players=3)]


def test_host_and_join_run_online_sessions() -> None:
    console, stream = _console()
    responses = iter(["Sam", "2", "", "", "3", "friend-ticket", "", "6"])
    played: list[PlayConfig] = []
    hosted: list[tuple[PlayConfig, str]] = []
    joined: list[tuple[str, str]] = []

    run_lobby(
        console=console,
        reader=lambda _prompt: next(responses),
        play=lambda *_args, **_kwargs: played.append(PlayConfig()) or 0,
        host=lambda config, **kwargs: (
            hosted.append((config, str(kwargs["display_name"])))
            or HostResult(winner=2, names=("Sam", "T1", "T2"))
        ),
        join=lambda ticket, **kwargs: (
            joined.append((ticket, str(kwargs["display_name"])))
            or GuestResult(winner=0, local_seat=1, names=("Host", "Sam"))
        ),
    )

    output = stream.getvalue()
    assert played == []
    assert hosted == [(PlayConfig(), "Sam")]
    assert joined == [("friend-ticket", "Sam")]
    assert "Host a table" in output
    assert "Join a table" in output
    assert "T2 won." in output
    assert "Seat 2" not in output
    assert "Host won." in output


def test_named_join_command_skips_ticket_prompt() -> None:
    console, stream = _console()
    responses = iter(["", "6"])

    run_lobby(
        console=console,
        reader=lambda _prompt: next(responses),
        display_name="Sam",
        opening=MenuOption.JOIN,
        join_ticket="abc123",
        play=lambda *_args, **_kwargs: 0,
        join=lambda *_args, **_kwargs: GuestResult(
            winner=1,
            local_seat=1,
            names=("Host", "Sam"),
        ),
    )

    output = stream.getvalue()
    assert "abc123" in output
    assert "See you at the table." in output


def test_invalid_menu_choice_retries() -> None:
    console, stream = _console()
    responses = iter(["Sam", "9", "6"])

    run_lobby(
        console=console,
        reader=lambda _prompt: next(responses),
        play=lambda *_args, **_kwargs: 0,
    )

    assert "Choose one of the listed numbers." in stream.getvalue()
