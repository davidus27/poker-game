"""52-card deck. Shuffle uses an injected RNG so deals are deterministic."""

from __future__ import annotations

import random

from holdem.domain.cards import Card, Rank, Suit
from holdem.engine.exceptions import EngineStateError


def standard_deck() -> list[Card]:
    return [Card(rank, suit) for suit in Suit for rank in Rank]


class Deck:
    def __init__(
        self,
        cards: list[Card] | None = None,
        *,
        rng: random.Random | None = None,
    ) -> None:
        if cards is not None:
            self._cards = list(cards)
        else:
            self._cards = standard_deck()
            (rng or random.Random()).shuffle(self._cards)

    def draw(self, n: int = 1) -> list[Card]:
        if n < 1:
            raise ValueError("draw count must be positive")
        if n > len(self._cards):
            raise EngineStateError("deck exhausted")
        drawn = self._cards[:n]
        del self._cards[:n]
        return drawn

    def remaining(self) -> tuple[Card, ...]:
        return tuple(self._cards)

    def __len__(self) -> int:
        return len(self._cards)
