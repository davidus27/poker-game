"""Side-pot construction and uncalled-bet return. Pure functions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pot:
    amount: int
    eligible: frozenset[int]


def return_uncalled(committed: dict[int, int]) -> dict[int, int]:
    """Return any uncalled excess to the unique highest contributor.

    Mutates a copy: the returned mapping is the committed amounts after
    the excess has been removed. The caller credits the difference back
    to that seat's stack.
    """
    if len(committed) < 2:
        return dict(committed)
    ordered = sorted(committed.values(), reverse=True)
    highest, second = ordered[0], ordered[1]
    if highest <= second:
        return dict(committed)
    adjusted = dict(committed)
    for seat_id, amount in committed.items():
        if amount == highest:
            adjusted[seat_id] = second
            break
    return adjusted


def build_pots(committed: dict[int, int], folded: set[int]) -> list[Pot]:
    """Layer side pots from committed amounts.

    Folded seats contribute chips but cannot win. Seats that committed
    nothing are ignored.
    """
    contributors = {seat: amount for seat, amount in committed.items() if amount > 0}
    if not contributors:
        return []

    levels = sorted(set(contributors.values()))
    pots: list[Pot] = []
    previous = 0
    for level in levels:
        layer = level - previous
        in_layer = [seat for seat, amount in contributors.items() if amount >= level]
        amount = layer * len(in_layer)
        eligible = frozenset(seat for seat in in_layer if seat not in folded)
        if amount > 0:
            pots.append(Pot(amount=amount, eligible=eligible))
        previous = level
    return pots
