"""Seeded replay of a full cash hand is deterministic."""

from __future__ import annotations

import random

from holdem.domain.actions import Action
from holdem.domain.events import Event, PotsAwarded, StreetDealt
from holdem.engine.table import Table
from tests.engine.helpers import play_script


def _run(seed: int) -> tuple[tuple[int, ...], tuple[Event, ...]]:
    table = Table(
        stacks=[200, 200, 200],
        small_blind=5,
        big_blind=10,
        rng=random.Random(seed),
    )
    events = play_script(
        table,
        {
            0: [Action.raise_to(30), Action.check(), Action.check(), Action.check()],
            1: [Action.call(), Action.check(), Action.check(), Action.check()],
            2: [Action.call(), Action.check(), Action.check(), Action.check()],
        },
    )
    return table.stacks_now(), tuple(events)


def test_same_seed_replays_identical_hand() -> None:
    stacks_a, events_a = _run(42)
    stacks_b, events_b = _run(42)
    assert stacks_a == stacks_b
    assert events_a == events_b
    assert any(isinstance(e, StreetDealt) for e in events_a)
    assert any(isinstance(e, PotsAwarded) for e in events_a)


def test_different_seed_can_diverge() -> None:
    stacks_a, events_a = _run(42)
    stacks_b, events_b = _run(99)
    # board / winner will almost certainly differ; stacks or events must
    assert stacks_a != stacks_b or events_a != events_b
