"""Host-authoritative online game loop, independent of the concrete transport."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from holdem.actors import Actor
from holdem.connectors import Connector, PeerDisconnected, PeerId
from holdem.domain import Action, ActionKind, Event, SeatStatus, SeatView, Street
from holdem.engine import IllegalAction, Table
from holdem.protocol import (
    ActionSubmitted,
    Envelope,
    ErrorMessage,
    State,
    Welcome,
    events_for_seat,
)
from holdem.ui.cli import PlayConfig
from holdem.ui.cli.renderer import RichView

DEFAULT_ACTION_TIMEOUT = 60.0
ActionSource = Callable[[SeatView], Action]
ContinueHand = Callable[[], None]


@dataclass(frozen=True)
class GuestResult:
    winner: int
    local_seat: int
    names: tuple[str, ...]


@dataclass(frozen=True)
class HostResult:
    winner: int
    names: tuple[str, ...]


async def play_host_session(
    config: PlayConfig,
    connector: Connector,
    guests: Mapping[PeerId, tuple[int, str]],
    *,
    bots: Mapping[int, Actor] | None = None,
    host_name: str,
    source: ActionSource,
    renderer: RichView,
    action_timeout: float | None = DEFAULT_ACTION_TIMEOUT,
    on_continue: ContinueHand | None = None,
) -> int:
    """Run the authoritative engine and service already-handshaken guests."""

    local_bots = {} if bots is None else bots
    guest_seats = {seat for seat, _name in guests.values()}
    bot_seats = set(local_bots)
    if 0 in bot_seats:
        raise ValueError("the host seat cannot be a bot")
    if guest_seats & bot_seats:
        raise ValueError("a seat cannot be both a guest and a bot")
    expected_seats = set(range(1, config.players))
    if guest_seats | bot_seats != expected_seats:
        raise ValueError("every non-host seat must be assigned to a guest or bot")

    table = Table(
        [config.starting_stack] * config.players,
        small_blind=config.small_blind,
        big_blind=config.big_blind,
        rng=random.Random(config.seed),
    )
    names = [host_name] + [f"Player {seat}" for seat in range(1, config.players)]
    for _peer, (seat, name) in guests.items():
        names[seat] = name
    for seat in local_bots:
        names[seat] = f"Bot {seat}"
    for peer, (seat, _name) in guests.items():
        await connector.send(
            peer,
            Envelope(Welcome(seat_id=seat, names=tuple(names), view=table.seat_view(seat))),
        )

    disconnected: set[PeerId] = set()
    events = table.start_hand()
    await _publish(table, events, connector, guests, renderer, disconnected)

    while not table.is_tournament_over:
        while table.to_act is not None:
            seat = table.to_act
            if seat == 0:
                action = source(table.seat_view(0))
            elif seat in local_bots:
                action = local_bots[seat].decide(table.seat_view(seat))
            else:
                peer = _peer_for_seat(guests, seat)
                action = await _remote_action(
                    connector,
                    guests,
                    table.seat_view(seat),
                    peer,
                    disconnected,
                    action_timeout,
                )
            try:
                events = table.apply(action)
            except IllegalAction:
                if seat == 0 or seat in local_bots:
                    raise
                peer = _peer_for_seat(guests, seat)
                await connector.send(peer, Envelope(ErrorMessage("That action is not legal.")))
                await connector.send(
                    peer,
                    Envelope(State((), table.seat_view(seat))),
                )
                continue
            await _publish(table, events, connector, guests, renderer, disconnected)
        if not table.is_tournament_over:
            if on_continue is not None:
                on_continue()
            events = table.start_hand()
            await _publish(table, events, connector, guests, renderer, disconnected)

    stacks = table.stacks_now()
    return max(range(len(stacks)), key=stacks.__getitem__)


async def play_guest_session(
    connector: Connector,
    host: PeerId,
    *,
    source: ActionSource,
    renderer_factory: Callable[[str, Mapping[int, str]], RichView],
    on_bust: Callable[[], bool] | None = None,
) -> GuestResult | None:
    """Render host snapshots and submit actions when this guest is requested."""

    peer, envelope = await connector.recv()
    if peer != host or not isinstance(envelope.payload, Welcome):
        raise ConnectionError("host did not send a valid welcome message")
    welcome = envelope.payload
    own_name = welcome.names[welcome.seat_id]
    seat_names = dict(enumerate(welcome.names))
    renderer = renderer_factory(own_name, seat_names)
    renderer.render((), welcome.view)
    spectating = False

    while True:
        peer, envelope = await connector.recv()
        if peer != host:
            continue
        payload = envelope.payload
        if isinstance(payload, ErrorMessage):
            continue
        if not isinstance(payload, State):
            raise ConnectionError(f"unexpected host message {envelope.type!r}")
        busted = _is_busted(payload.view)
        renderer.render(payload.events, payload.view, spectating=spectating or busted)
        if payload.view.street is Street.TOURNAMENT_OVER:
            winner = max(payload.view.seats, key=lambda seat: seat.stack).seat_id
            return GuestResult(
                winner=winner,
                local_seat=welcome.seat_id,
                names=welcome.names,
            )
        if busted and not spectating:
            if on_bust is not None and not on_bust():
                return None
            spectating = True
        if payload.view.to_act == payload.view.seat_id:
            await connector.send(host, Envelope(ActionSubmitted(source(payload.view))))


async def _publish(
    table: Table,
    events: Sequence[Event],
    connector: Connector,
    guests: Mapping[PeerId, tuple[int, str]],
    renderer: RichView,
    disconnected: set[PeerId],
) -> None:
    host_view = table.seat_view(0)
    renderer.render(
        events_for_seat(events, 0),
        host_view,
        spectating=_is_busted(host_view),
    )
    for peer, (seat, _name) in guests.items():
        if peer in disconnected:
            continue
        try:
            await connector.send(
                peer,
                Envelope(State(events_for_seat(events, seat), table.seat_view(seat))),
            )
        except PeerDisconnected:
            disconnected.add(peer)


async def _remote_action(
    connector: Connector,
    guests: Mapping[PeerId, tuple[int, str]],
    view: SeatView,
    expected_peer: PeerId,
    disconnected: set[PeerId],
    timeout: float | None,
) -> Action:
    if expected_peer in disconnected:
        return _safe_default(view)
    while True:
        try:
            receive = connector.recv()
            peer, envelope = (
                await receive if timeout is None else await asyncio.wait_for(receive, timeout)
            )
        except TimeoutError:
            return _safe_default(view)
        except PeerDisconnected as exc:
            disconnected.add(exc.peer)
            if exc.peer == expected_peer:
                return _safe_default(view)
            continue
        assignment = guests.get(peer)
        if assignment is None or peer != expected_peer:
            await connector.send(peer, Envelope(ErrorMessage("It is not your turn.")))
            continue
        if not isinstance(envelope.payload, ActionSubmitted):
            await connector.send(peer, Envelope(ErrorMessage("An action was expected.")))
            continue
        return envelope.payload.action


def _safe_default(view: SeatView) -> Action:
    legal = {choice.kind for choice in view.legal_actions}
    if ActionKind.FOLD in legal:
        return Action.fold()
    if ActionKind.CHECK in legal:
        return Action.check()
    if ActionKind.CALL in legal:
        return Action.call()
    return Action.all_in()


def _peer_for_seat(
    guests: Mapping[PeerId, tuple[int, str]],
    seat_id: int,
) -> PeerId:
    for peer, (seat, _name) in guests.items():
        if seat == seat_id:
            return peer
    raise ConnectionError(f"seat {seat_id} has no connected peer")


def _is_busted(view: SeatView) -> bool:
    return (
        next(seat for seat in view.seats if seat.seat_id == view.seat_id).status
        is SeatStatus.BUSTED
    )
