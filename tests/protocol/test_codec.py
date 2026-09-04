"""Protocol round trips and privacy boundaries."""

from __future__ import annotations

import pytest

from holdem.domain import Action, HoleDealt
from holdem.engine import Table
from holdem.protocol import (
    ActionSubmitted,
    Envelope,
    ErrorMessage,
    Hello,
    ProtocolError,
    State,
    Welcome,
    decode_envelope,
    encode_envelope,
    events_for_seat,
)


def test_every_envelope_kind_round_trips() -> None:
    table = Table([100, 100], small_blind=1, big_blind=2)
    events = table.start_hand()
    view = table.seat_view(0)
    envelopes = (
        Envelope(Hello("Ada")),
        Envelope(Welcome(0, ("Ada", "Bob"), view)),
        Envelope(State(tuple(events_for_seat(events, 0)), view)),
        Envelope(ActionSubmitted(Action.raise_to(12))),
        Envelope(ErrorMessage("bad action")),
    )

    for envelope in envelopes:
        assert decode_envelope(encode_envelope(envelope)) == envelope


def test_state_codec_round_trips_a_complete_showdown_event_set() -> None:
    table = Table([20, 20], small_blind=1, big_blind=2)
    events = table.start_hand()
    all_events = list(events)
    while table.to_act is not None:
        action = Action.all_in()
        emitted = table.apply(action)
        all_events.extend(emitted)

    envelope = Envelope(State(tuple(events_for_seat(all_events, 0)), table.seat_view(0)))

    assert decode_envelope(encode_envelope(envelope)) == envelope


def test_foreign_hole_events_are_removed() -> None:
    table = Table([100, 100, 100])
    events = table.start_hand()

    private = events_for_seat(events, 1)
    deals = [event for event in private if isinstance(event, HoleDealt)]

    assert len(deals) == 1
    assert deals[0].seat_id == 1


def test_unknown_version_and_message_type_are_rejected() -> None:
    with pytest.raises(ProtocolError, match="unsupported protocol version"):
        decode_envelope('{"v":2,"type":"hello","payload":{"name":"Ada"}}')
    with pytest.raises(ProtocolError, match="unknown message type"):
        decode_envelope('{"v":1,"type":"mystery","payload":{}}')
