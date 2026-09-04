"""Deterministic in-process connector for application and protocol tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from holdem.connectors.protocols import (
    ConnectorClosed,
    PeerDisconnected,
    PeerId,
)
from holdem.protocol import Envelope

_CLOSED = object()


@dataclass(frozen=True)
class _Packet:
    sender: PeerId
    envelope: Envelope


class InMemoryConnector:
    """One endpoint of an in-memory, ordered, point-to-point connection."""

    def __init__(
        self,
        local_id: PeerId,
        remote_id: PeerId,
        inbox: asyncio.Queue[_Packet | object],
        outbox: asyncio.Queue[_Packet | object],
    ) -> None:
        self.local_id = local_id
        self.remote_id = remote_id
        self._inbox = inbox
        self._outbox = outbox
        self._closed = False

    @classmethod
    def pair(
        cls,
        first_id: str = "host",
        second_id: str = "guest",
    ) -> tuple[InMemoryConnector, InMemoryConnector]:
        """Create two connected endpoints."""

        first_inbox: asyncio.Queue[_Packet | object] = asyncio.Queue()
        second_inbox: asyncio.Queue[_Packet | object] = asyncio.Queue()
        first = cls(PeerId(first_id), PeerId(second_id), first_inbox, second_inbox)
        second = cls(PeerId(second_id), PeerId(first_id), second_inbox, first_inbox)
        return first, second

    async def send(self, peer: PeerId, envelope: Envelope) -> None:
        if self._closed:
            raise ConnectorClosed("connector is closed")
        if peer != self.remote_id:
            raise ValueError(f"unknown peer {peer}")
        await self._outbox.put(_Packet(self.local_id, envelope))

    async def recv(self) -> tuple[PeerId, Envelope]:
        if self._closed and self._inbox.empty():
            raise ConnectorClosed("connector is closed")
        packet = await self._inbox.get()
        if packet is _CLOSED:
            raise PeerDisconnected(self.remote_id)
        assert isinstance(packet, _Packet)
        return packet.sender, packet.envelope

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            await self._outbox.put(_CLOSED)
