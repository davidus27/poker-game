"""Iroh 1.x connector using one framed bidirectional stream per peer."""

from __future__ import annotations

import asyncio
import importlib
import struct
from dataclasses import dataclass
from typing import Any

from holdem.connectors.protocols import (
    ConnectorClosed,
    PeerDisconnected,
    PeerId,
)
from holdem.protocol import Envelope, decode_envelope, encode_envelope

ALPN = b"holdem/1"
MAX_FRAME_SIZE = 1_048_576
_HEADER = struct.Struct("!I")


class IrohUnavailable(RuntimeError):
    """The optional Iroh runtime is not installed."""


@dataclass
class _Peer:
    connection: Any
    sender: Any
    receiver: Any
    send_lock: asyncio.Lock
    reader_task: asyncio.Task[None]


class IrohConnector:
    """Multi-peer Iroh endpoint carrying protocol envelopes."""

    def __init__(self, endpoint: Any) -> None:
        self._endpoint = endpoint
        self._peers: dict[PeerId, _Peer] = {}
        self._inbox: asyncio.Queue[tuple[PeerId, Envelope] | PeerDisconnected | ConnectorClosed] = (
            asyncio.Queue()
        )
        self._closed = False

    @classmethod
    async def host(cls) -> tuple[IrohConnector, str]:
        """Bind a host endpoint and return its shareable endpoint ticket."""

        iroh = _load_iroh()
        _set_iroh_loop(iroh)
        options = iroh.EndpointOptions(preset=iroh.preset_n0(), alpns=[ALPN])
        endpoint = await iroh.Endpoint.bind(options)
        ticket = str(iroh.EndpointTicket.from_addr(endpoint.addr()))
        return cls(endpoint), ticket

    @classmethod
    async def join(cls, ticket: str) -> tuple[IrohConnector, PeerId]:
        """Bind a guest endpoint and connect it to a host ticket."""

        iroh = _load_iroh()
        _set_iroh_loop(iroh)
        endpoint = await iroh.Endpoint.bind(iroh.EndpointOptions(preset=iroh.preset_n0()))
        try:
            address = iroh.EndpointTicket.from_string(ticket).endpoint_addr()
            connection = await endpoint.connect(address, ALPN)
            connector = cls(endpoint)
            peer = await connector._attach(connection, opens_stream=True)
            return connector, peer
        except BaseException:
            await endpoint.close()
            raise

    async def accept_peer(self) -> PeerId:
        """Accept one incoming Iroh connection and begin receiving its frames."""

        if self._closed:
            raise ConnectorClosed("connector is closed")
        incoming = await self._endpoint.accept_next()
        if incoming is None:
            raise ConnectorClosed("endpoint closed while accepting a peer")
        connection = await (await incoming.accept()).connect()
        return await self._attach(connection, opens_stream=False)

    async def _attach(self, connection: Any, *, opens_stream: bool) -> PeerId:
        peer = PeerId(str(connection.remote_id()))
        if peer in self._peers:
            connection.close(1, b"duplicate peer")
            raise ConnectionError(f"peer {peer} is already connected")
        stream = await connection.open_bi() if opens_stream else await connection.accept_bi()
        sender = stream.send()
        receiver = stream.recv()
        placeholder = asyncio.create_task(asyncio.sleep(0))
        record = _Peer(connection, sender, receiver, asyncio.Lock(), placeholder)
        self._peers[peer] = record
        record.reader_task = asyncio.create_task(
            self._read_frames(peer, receiver),
            name=f"holdem-iroh-reader-{peer}",
        )
        return peer

    async def send(self, peer: PeerId, envelope: Envelope) -> None:
        if self._closed:
            raise ConnectorClosed("connector is closed")
        record = self._peers.get(peer)
        if record is None:
            raise ValueError(f"unknown peer {peer}")
        payload = encode_envelope(envelope)
        if len(payload) > MAX_FRAME_SIZE:
            raise ValueError("protocol frame exceeds maximum size")
        frame = _HEADER.pack(len(payload)) + payload
        try:
            async with record.send_lock:
                await record.sender.write_all(frame)
        except Exception as exc:
            raise PeerDisconnected(peer) from exc

    async def recv(self) -> tuple[PeerId, Envelope]:
        if self._closed and self._inbox.empty():
            raise ConnectorClosed("connector is closed")
        item = await self._inbox.get()
        if isinstance(item, (PeerDisconnected, ConnectorClosed)):
            raise item
        return item

    async def _read_frames(self, peer: PeerId, receiver: Any) -> None:
        try:
            while True:
                header = bytes(await receiver.read_exact(_HEADER.size))
                (size,) = _HEADER.unpack(header)
                if size > MAX_FRAME_SIZE:
                    raise ValueError("received protocol frame exceeds maximum size")
                payload = bytes(await receiver.read_exact(size))
                await self._inbox.put((peer, decode_envelope(payload)))
        except asyncio.CancelledError:
            raise
        except Exception:
            if not self._closed:
                await self._inbox.put(PeerDisconnected(peer))

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        peers = tuple(self._peers.values())
        for peer in peers:
            peer.reader_task.cancel()
            peer.connection.close(0, b"holdem session closed")
        if peers:
            await asyncio.gather(
                *(peer.reader_task for peer in peers),
                return_exceptions=True,
            )
        await self._endpoint.close()
        await self._inbox.put(ConnectorClosed("connector is closed"))


def _load_iroh() -> Any:
    try:
        return importlib.import_module("iroh")
    except ImportError as exc:
        raise IrohUnavailable(
            'Online play requires Iroh. Install it with: pip install -e ".[network]"'
        ) from exc


def _set_iroh_loop(iroh: Any) -> None:
    iroh.iroh_ffi.uniffi_set_event_loop(asyncio.get_running_loop())
