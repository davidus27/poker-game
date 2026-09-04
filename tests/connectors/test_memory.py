"""In-memory transport behavior."""

from __future__ import annotations

import asyncio

import pytest

from holdem.connectors import InMemoryConnector, PeerDisconnected
from holdem.protocol import Envelope, Hello


def test_pair_sends_envelopes_in_both_directions() -> None:
    async def scenario() -> None:
        host, guest = InMemoryConnector.pair()
        first = Envelope(Hello("guest"))
        second = Envelope(Hello("host"))

        await guest.send(guest.remote_id, first)
        assert await host.recv() == (guest.local_id, first)
        await host.send(host.remote_id, second)
        assert await guest.recv() == (host.local_id, second)

    asyncio.run(scenario())


def test_close_notifies_the_other_endpoint() -> None:
    async def scenario() -> None:
        host, guest = InMemoryConnector.pair()
        await guest.close()
        with pytest.raises(PeerDisconnected) as caught:
            await host.recv()
        assert caught.value.peer == guest.local_id

    asyncio.run(scenario())
