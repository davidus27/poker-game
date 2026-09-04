"""A full host/guest hand over the transport-independent runner."""

from __future__ import annotations

import asyncio

from holdem.app.online import play_guest_session, play_host_session
from holdem.connectors import InMemoryConnector
from holdem.domain import Action, SeatView
from holdem.ui.cli import PlayConfig


class _View:
    def __init__(self) -> None:
        self.snapshots: list[SeatView] = []

    def render(self, _events: object, view: SeatView) -> None:
        self.snapshots.append(view)


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

        assert host_winner == guest_result.winner
        assert guest_result.local_seat == 1
        assert guest_result.names == ("Host", "Guest")
        assert host_view.snapshots
        assert guest_views[0].snapshots
        assert all(len(view.hole) in {0, 2} for view in guest_views[0].snapshots)

    asyncio.run(scenario())
