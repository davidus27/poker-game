"""Local play loop presentation details."""

from __future__ import annotations

from io import StringIO

from pytest import MonkeyPatch
from rich.console import Console

from holdem.actors import BotDifficulty
from holdem.app import play as play_mod
from holdem.domain import Action, ActionKind, SeatView
from holdem.ui.cli import PlayConfig


class _SafeHuman:
    def __init__(self, **_kwargs: object) -> None:
        return

    def __call__(self, view: SeatView) -> Action:
        kinds = {legal.kind: legal for legal in view.legal_actions}
        if ActionKind.FOLD in kinds:
            return Action.fold()
        if ActionKind.CHECK in kinds:
            return Action.check()
        return Action.call()


def test_bot_turns_pause_for_thinking_and_reveal(monkeypatch: MonkeyPatch) -> None:
    pauses: list[float] = []
    monkeypatch.setattr(play_mod, "RichActionSource", _SafeHuman)
    console = Console(file=StringIO(), force_terminal=False, width=100)

    winner = play_mod.play_local(
        PlayConfig(players=2, starting_stack=50, small_blind=1, big_blind=2, seed=1),
        console=console,
        pause=pauses.append,
        on_continue=lambda: None,
    )

    assert winner in {0, 1}
    thinks = [pause for pause in pauses if pause != play_mod.BOT_REVEAL_PAUSE]
    reveals = [pause for pause in pauses if pause == play_mod.BOT_REVEAL_PAUSE]
    assert thinks
    assert reveals
    assert all(play_mod.BOT_THINK_MIN <= pause <= play_mod.BOT_THINK_MAX for pause in thinks)


def test_busted_human_can_leave_instead_of_watching_bots(monkeypatch: MonkeyPatch) -> None:
    asked = {"n": 0}
    monkeypatch.setattr(play_mod, "RichActionSource", _SafeHuman)
    console = Console(file=StringIO(), force_terminal=False, width=100)

    def leave() -> bool:
        asked["n"] += 1
        return False

    result = play_mod.play_local(
        PlayConfig(players=4, starting_stack=40, small_blind=5, big_blind=10, seed=0),
        console=console,
        pause=lambda _seconds: None,
        on_bust=leave,
        on_continue=lambda: None,
    )

    assert asked["n"] == 1
    assert result is None


def test_busted_human_can_spectate_until_a_bot_wins(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(play_mod, "RichActionSource", _SafeHuman)
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=100)

    result = play_mod.play_local(
        PlayConfig(players=4, starting_stack=40, small_blind=5, big_blind=10, seed=0),
        console=console,
        pause=lambda _seconds: None,
        on_bust=lambda: True,
        on_continue=lambda: None,
    )

    assert result in {1, 2, 3}
    assert "Spectating the rest of the table." in stream.getvalue()


def test_hand_result_waits_before_the_next_deal(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(play_mod, "RichActionSource", _SafeHuman)
    prompts: list[str] = []

    def reader(prompt: str) -> str:
        prompts.append(prompt)
        return ""

    console = Console(file=StringIO(), force_terminal=False, width=100)
    play_mod.play_local(
        PlayConfig(players=2, starting_stack=50, small_blind=1, big_blind=2, seed=1),
        console=console,
        reader=reader,
        pause=lambda _seconds: None,
    )

    assert any("next hand" in prompt.lower() for prompt in prompts)


def test_local_play_uses_configured_bot_difficulty(monkeypatch: MonkeyPatch) -> None:
    created: list[BotDifficulty] = []
    real_make_bot = play_mod.make_bot

    def tracking_make_bot(difficulty: BotDifficulty, rng: object = None) -> object:
        created.append(difficulty)
        return real_make_bot(difficulty, rng)

    monkeypatch.setattr(play_mod, "make_bot", tracking_make_bot)
    monkeypatch.setattr(play_mod, "RichActionSource", _SafeHuman)
    console = Console(file=StringIO(), force_terminal=False, width=100)

    play_mod.play_local(
        PlayConfig(
            players=2,
            starting_stack=50,
            small_blind=1,
            big_blind=2,
            seed=1,
            difficulty=BotDifficulty.HARD,
        ),
        console=console,
        pause=lambda _seconds: None,
        on_continue=lambda: None,
    )

    assert created == [BotDifficulty.HARD]
