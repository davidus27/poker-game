"""Lobby intro, menu, and placeholder host/join flows."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from holdem.app.lobby import run_lobby
from holdem.ui.cli import MenuOption, PlayConfig
from holdem.ui.cli.lobby import ONLINE_UNAVAILABLE


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


def test_host_and_join_show_coming_soon_without_starting_a_game() -> None:
    console, stream = _console()
    responses = iter(["Sam", "2", "", "", "3", "friend-ticket", "", "6"])
    played: list[PlayConfig] = []

    run_lobby(
        console=console,
        reader=lambda _prompt: next(responses),
        play=lambda *_args, **_kwargs: played.append(PlayConfig()) or 0,
    )

    output = stream.getvalue()
    assert played == []
    assert "Host a table" in output
    assert "Join a table" in output
    assert "friend-ticket" in output
    assert ONLINE_UNAVAILABLE in output


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
    )

    output = stream.getvalue()
    assert "abc123" in output
    assert ONLINE_UNAVAILABLE in output
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
