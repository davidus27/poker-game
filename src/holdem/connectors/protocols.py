"""Transport boundary used by online application runners."""

from __future__ import annotations

from typing import NewType, Protocol

from holdem.protocol import Envelope

PeerId = NewType("PeerId", str)


class ConnectorClosed(ConnectionError):
    """The connector was closed before another message arrived."""


class PeerDisconnected(ConnectionError):
    """A connected peer can no longer exchange messages."""

    def __init__(self, peer: PeerId) -> None:
        self.peer = peer
        super().__init__(f"peer {peer} disconnected")


class Connector(Protocol):
    async def send(self, peer: PeerId, envelope: Envelope) -> None:
        """Send one envelope to a connected peer."""
        ...

    async def recv(self) -> tuple[PeerId, Envelope]:
        """Wait for the next envelope from any connected peer."""
        ...

    async def close(self) -> None:
        """Close this endpoint and release transport resources."""
        ...
