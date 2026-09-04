"""A full host/guest hand over the transport-independent runner."""

from __future__ import annotations

import asyncio
from dataclasses import replace

from holdem.actors import ScriptedActor
from holdem.app.host import collect_guests
from holdem.app.online import play_guest_session, play_host_session
from holdem.connectors import InMemoryConnector, PeerId
from holdem.domain import Action, HoleDealt, SeatView, Street
from holdem.engine import Table
from holdem.protocol import Envelope, State, Welcome
from holdem.ui.cli import PlayConfig


class _View:
    def __init__(self) -> None:
        self.snapshots: list[SeatView] = []
        self.events: list[object] = []

    def render(
        self,
        events: object,
        view: SeatView,
        **_kwargs: object,
    ) -> None:
        self.snapshots.append(view)
        self.events.extend(events)  # type: ignore[arg-type]


def test_in_memory_host_guest_play_a_full_tournament() -> None:
    async def scenario() -> None:
        host_connector, guest_connector = InMemoryConnector.pair()
        host_view = _View()
        guest_views: list[_View] = []

        def guest_renderer(_name: str, _names: object) -> _View:
            renderer = _View()
            guest_views.append(renderer)
            return renderer

        def shove(_view: SeatView) -> Action:
            return Action.all_in()

        host_game = play_host_session(
            PlayConfig(players=2, starting_stack=20, small_blind=1, big_blind=2, seed=4),
            host_connector,
            {host_connector.remote_id: (1, "Guest")},
            host_name="Host",
            source=shove,
            renderer=host_view,  # type: ignore[arg-type]
            action_timeout=None,
        )
        guest_game = play_guest_session(
            guest_connector,
            guest_connector.remote_id,
            source=shove,
            renderer_factory=guest_renderer,  # type: ignore[arg-type]
        )
        host_winner, guest_result = await asyncio.gather(host_game, guest_game)

        assert guest_result is not None
        assert host_winner == guest_result.winner
        assert guest_result.local_seat == 1
        assert guest_result.names == ("Host", "Guest")
        assert host_view.snapshots
        assert guest_views[0].snapshots
        assert all(len(view.hole) in {0, 2} for view in guest_views[0].snapshots)

    asyncio.run(scenario())


def test_collect_guests_starts_early_after_one_join() -> None:
    async def scenario() -> None:
        start = asyncio.Event()
        waiting = asyncio.Event()

        async def accept_one() -> tuple[PeerId, str]:
            if not waiting.is_set():
                waiting.set()
                start.set()
                return PeerId("guest-1"), "Guest"
            await asyncio.Future()
            raise AssertionError("unreachable")

        guests = await collect_guests(2, accept_one, start)

        assert guests == {PeerId("guest-1"): (1, "Guest")}

    asyncio.run(scenario())


def test_in_memory_mixed_table_runs_bot_locally_and_keeps_guest_holes_private() -> None:
    async def scenario() -> None:
        host_connector, guest_connector = InMemoryConnector.pair()
        host_view = _View()
        guest_views: list[_View] = []

        def guest_renderer(_name: str, _names: object) -> _View:
            renderer = _View()
            guest_views.append(renderer)
            return renderer

        def shove(_view: SeatView) -> Action:
            return Action.all_in()

        config = PlayConfig(
            players=3,
            starting_stack=20,
            small_blind=1,
            big_blind=2,
            seed=8,
            bots=1,
        )
        bot = ScriptedActor([Action.all_in()] * 100)
        host_game = play_host_session(
            config,
            host_connector,
            {host_connector.remote_id: (1, "Guest")},
            bots={2: bot},
            host_name="Host",
            source=shove,
            renderer=host_view,  # type: ignore[arg-type]
            action_timeout=None,
        )
        guest_game = play_guest_session(
            guest_connector,
            guest_connector.remote_id,
            source=shove,
            renderer_factory=guest_renderer,  # type: ignore[arg-type]
        )
        host_winner, guest_result = await asyncio.gather(host_game, guest_game)

        assert guest_result is not None
        assert host_winner == guest_result.winner
        assert guest_result.names == ("Host", "Guest", "Bot 2")
        assert bot.remaining < 100
        assert guest_views[0].snapshots
        assert all(
            not isinstance(event, HoleDealt) or event.seat_id == 1
            for event in guest_views[0].events
        )

    asyncio.run(scenario())


def test_busted_guest_can_leave_while_the_table_continues() -> None:
    async def scenario() -> None:
        host, guest = InMemoryConnector.pair()
        renderer = _View()
        busted = replace(
            Table([100, 0, 100]).seat_view(1),
            street=Street.HAND_OVER,
        )
        guest_game = asyncio.create_task(
            play_guest_session(
                guest,
                guest.remote_id,
                source=lambda _view: Action.check(),
                renderer_factory=lambda _name, _names: renderer,  # type: ignore[arg-type]
                on_bust=lambda: False,
            )
        )

        await host.send(
            host.remote_id,
            Envelope(Welcome(1, ("Host", "Guest", "Other"), busted)),
        )
        await host.send(host.remote_id, Envelope(State((), busted)))

        assert await guest_game is None
        assert renderer.snapshots[-1] == busted

    asyncio.run(scenario())
