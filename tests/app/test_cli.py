"""CLI command composition."""

from __future__ import annotations

import pytest
from pytest import MonkeyPatch

from holdem.app import cli
from holdem.ui.cli import MenuOption, PlayConfig


def test_play_command_opens_lobby(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_lobby(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(cli, "run_lobby", fake_lobby)

    cli.main(["play"])

    assert captured["table"] == PlayConfig()
    assert captured["display_name"] is None
    assert captured["opening"] is None
    assert captured["join_ticket"] is None


def test_no_command_opens_lobby(monkeypatch: MonkeyPatch) -> None:
    called = {"n": 0}

    def fake_lobby(**kwargs: object) -> None:
        called["n"] += 1

    monkeypatch.setattr(cli, "run_lobby", fake_lobby)

    cli.main([])

    assert called["n"] == 1


def test_flags_prefill_table_and_name(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_lobby(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(cli, "run_lobby", fake_lobby)

    cli.main(
        [
            "play",
            "--players",
            "3",
            "--stack",
            "100",
            "--blinds",
            "5/10",
            "--seed",
            "7",
            "--name",
            "Dave",
        ]
    )

    assert captured["table"] == PlayConfig(3, 100, 5, 10, seed=7)
    assert captured["display_name"] == "Dave"


def test_host_and_join_commands_open_placeholder_flows(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_lobby(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(cli, "run_lobby", fake_lobby)

    cli.main(["host"])
    assert captured["opening"] is MenuOption.HOST

    cli.main(["join", "ticket-one"])
    assert captured["opening"] is MenuOption.JOIN
    assert captured["join_ticket"] == "ticket-one"


def test_play_command_rejects_stack_smaller_than_big_blind(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as caught:
        cli.main(["play", "--stack", "2", "--blinds", "5/10"])

    assert caught.value.code == 2
    assert "starting stack must cover the big blind" in capsys.readouterr().err
