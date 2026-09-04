"""Player actions submitted to the engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionKind(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass(frozen=True)
class Action:
    """A decision from the seat to act.

    For ``RAISE``, ``amount`` is the street total to raise *to* (not by).
    Other kinds ignore ``amount``.
    """

    kind: ActionKind
    amount: int | None = None

    @staticmethod
    def fold() -> Action:
        return Action(ActionKind.FOLD)

    @staticmethod
    def check() -> Action:
        return Action(ActionKind.CHECK)

    @staticmethod
    def call() -> Action:
        return Action(ActionKind.CALL)

    @staticmethod
    def raise_to(amount: int) -> Action:
        if amount <= 0:
            raise ValueError("raise amount must be positive")
        return Action(ActionKind.RAISE, amount)

    @staticmethod
    def all_in() -> Action:
        return Action(ActionKind.ALL_IN)
