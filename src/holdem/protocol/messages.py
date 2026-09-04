"""Versioned, transport-independent messages exchanged by online peers."""

from __future__ import annotations

from dataclasses import dataclass

from holdem.domain.actions import Action
from holdem.domain.events import Event
from holdem.domain.views import SeatView

PROTOCOL_VERSION = 1


@dataclass(frozen=True)
class Hello:
    name: str


@dataclass(frozen=True)
class Welcome:
    seat_id: int
    names: tuple[str, ...]
    view: SeatView


@dataclass(frozen=True)
class State:
    events: tuple[Event, ...]
    view: SeatView


@dataclass(frozen=True)
class ActionSubmitted:
    action: Action


@dataclass(frozen=True)
class ErrorMessage:
    message: str


Payload = Hello | Welcome | State | ActionSubmitted | ErrorMessage


@dataclass(frozen=True)
class Envelope:
    """A protocol message with an explicit compatibility version."""

    payload: Payload
    version: int = PROTOCOL_VERSION

    @property
    def type(self) -> str:
        return {
            Hello: "hello",
            Welcome: "welcome",
            State: "state",
            ActionSubmitted: "action",
            ErrorMessage: "error",
        }[type(self.payload)]
