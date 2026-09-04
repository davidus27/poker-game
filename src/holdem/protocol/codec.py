"""JSON codec for protocol envelopes and domain value objects."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, NoReturn

from holdem.domain.actions import Action, ActionKind
from holdem.domain.cards import Card, HandRank, HandScore, format_card, parse_card
from holdem.domain.events import (
    ActionRequested,
    BlindKind,
    BlindPosted,
    Event,
    HandEnded,
    HandStarted,
    HoleDealt,
    PlayerActed,
    PlayerBusted,
    PotAward,
    PotsAwarded,
    Showdown,
    ShowdownHand,
    StreetDealt,
    TournamentEnded,
)
from holdem.domain.views import (
    LegalAction,
    PotView,
    PublicSeat,
    SeatStatus,
    SeatView,
    Street,
)
from holdem.protocol.messages import (
    PROTOCOL_VERSION,
    ActionSubmitted,
    Envelope,
    ErrorMessage,
    Hello,
    Payload,
    State,
    Welcome,
)


class ProtocolError(ValueError):
    """A malformed or incompatible wire message."""


def encode_envelope(envelope: Envelope) -> bytes:
    """Encode an envelope as compact UTF-8 JSON."""

    body = {
        "v": envelope.version,
        "type": envelope.type,
        "payload": _encode_payload(envelope.payload),
    }
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")


def decode_envelope(data: bytes | str) -> Envelope:
    """Decode and validate one envelope."""

    try:
        raw = json.loads(data)
        obj = _mapping(raw, "envelope")
        version = _integer(obj.get("v"), "v")
        if version != PROTOCOL_VERSION:
            raise ProtocolError(
                f"unsupported protocol version {version}; expected {PROTOCOL_VERSION}"
            )
        kind = _string(obj.get("type"), "type")
        payload = _mapping(obj.get("payload"), "payload")
        return Envelope(_decode_payload(kind, payload), version=version)
    except ProtocolError:
        raise
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"invalid protocol message: {exc}") from exc


def _encode_payload(payload: object) -> dict[str, Any]:
    if isinstance(payload, Hello):
        return {"name": payload.name}
    if isinstance(payload, Welcome):
        return {
            "seat_id": payload.seat_id,
            "names": list(payload.names),
            "view": _encode_view(payload.view),
        }
    if isinstance(payload, State):
        return {
            "events": [_encode_event(event) for event in payload.events],
            "view": _encode_view(payload.view),
        }
    if isinstance(payload, ActionSubmitted):
        return {"action": _encode_action(payload.action)}
    if isinstance(payload, ErrorMessage):
        return {"message": payload.message}
    raise TypeError(f"unsupported payload {type(payload).__name__}")


def _decode_payload(kind: str, payload: Mapping[str, object]) -> Payload:
    if kind == "hello":
        return Hello(_string(payload.get("name"), "name"))
    if kind == "welcome":
        return Welcome(
            seat_id=_integer(payload.get("seat_id"), "seat_id"),
            names=tuple(_string(name, "name") for name in _sequence(payload.get("names"), "names")),
            view=_decode_view(_mapping(payload.get("view"), "view")),
        )
    if kind == "state":
        return State(
            events=tuple(
                _decode_event(_mapping(event, "event"))
                for event in _sequence(payload.get("events"), "events")
            ),
            view=_decode_view(_mapping(payload.get("view"), "view")),
        )
    if kind == "action":
        return ActionSubmitted(_decode_action(_mapping(payload.get("action"), "action")))
    if kind == "error":
        return ErrorMessage(_string(payload.get("message"), "message"))
    raise ProtocolError(f"unknown message type {kind!r}")


def _encode_action(action: Action) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": action.kind.value}
    if action.amount is not None:
        result["amount"] = action.amount
    return result


def _decode_action(raw: Mapping[str, object]) -> Action:
    kind = ActionKind(_string(raw.get("kind"), "action.kind"))
    amount_obj = raw.get("amount")
    amount = None if amount_obj is None else _integer(amount_obj, "action.amount")
    if kind is ActionKind.RAISE:
        if amount is None:
            raise ProtocolError("raise action requires amount")
        return Action.raise_to(amount)
    if amount is not None:
        raise ProtocolError(f"{kind.value} action must not include amount")
    return Action(kind)


def _encode_view(view: SeatView) -> dict[str, Any]:
    return {
        "seat_id": view.seat_id,
        "street": view.street.value,
        "hand_number": view.hand_number,
        "button": view.button,
        "small_blind": view.small_blind,
        "big_blind": view.big_blind,
        "board": [_card(card) for card in view.board],
        "hole": [_card(card) for card in view.hole],
        "pot_total": view.pot_total,
        "pots": [{"amount": pot.amount, "eligible": sorted(pot.eligible)} for pot in view.pots],
        "seats": [
            {
                "seat_id": seat.seat_id,
                "stack": seat.stack,
                "status": seat.status.value,
                "street_bet": seat.street_bet,
                "committed": seat.committed,
            }
            for seat in view.seats
        ],
        "to_act": view.to_act,
        "legal_actions": [
            {
                "kind": legal.kind.value,
                "min_amount": legal.min_amount,
                "max_amount": legal.max_amount,
            }
            for legal in view.legal_actions
        ],
        "current_bet": view.current_bet,
        "min_raise_to": view.min_raise_to,
    }


def _decode_view(raw: Mapping[str, object]) -> SeatView:
    to_act_obj = raw.get("to_act")
    min_raise_obj = raw.get("min_raise_to")
    return SeatView(
        seat_id=_integer(raw.get("seat_id"), "view.seat_id"),
        street=Street(_string(raw.get("street"), "view.street")),
        hand_number=_integer(raw.get("hand_number"), "view.hand_number"),
        button=_integer(raw.get("button"), "view.button"),
        small_blind=_integer(raw.get("small_blind"), "view.small_blind"),
        big_blind=_integer(raw.get("big_blind"), "view.big_blind"),
        board=tuple(_cards(raw.get("board"), "view.board")),
        hole=tuple(_cards(raw.get("hole"), "view.hole")),
        pot_total=_integer(raw.get("pot_total"), "view.pot_total"),
        pots=tuple(
            PotView(
                amount=_integer(pot.get("amount"), "pot.amount"),
                eligible=frozenset(
                    _integer(seat, "pot.eligible")
                    for seat in _sequence(pot.get("eligible"), "pot.eligible")
                ),
            )
            for item in _sequence(raw.get("pots"), "view.pots")
            for pot in [_mapping(item, "pot")]
        ),
        seats=tuple(
            PublicSeat(
                seat_id=_integer(seat.get("seat_id"), "seat.seat_id"),
                stack=_integer(seat.get("stack"), "seat.stack"),
                status=SeatStatus(_string(seat.get("status"), "seat.status")),
                street_bet=_integer(seat.get("street_bet"), "seat.street_bet"),
                committed=_integer(seat.get("committed"), "seat.committed"),
            )
            for item in _sequence(raw.get("seats"), "view.seats")
            for seat in [_mapping(item, "seat")]
        ),
        to_act=None if to_act_obj is None else _integer(to_act_obj, "view.to_act"),
        legal_actions=tuple(
            LegalAction(
                kind=ActionKind(_string(legal.get("kind"), "legal.kind")),
                min_amount=_optional_int(legal.get("min_amount"), "legal.min_amount"),
                max_amount=_optional_int(legal.get("max_amount"), "legal.max_amount"),
            )
            for item in _sequence(raw.get("legal_actions"), "view.legal_actions")
            for legal in [_mapping(item, "legal action")]
        ),
        current_bet=_integer(raw.get("current_bet"), "view.current_bet"),
        min_raise_to=(
            None if min_raise_obj is None else _integer(min_raise_obj, "view.min_raise_to")
        ),
    )


def _encode_event(event: Event) -> dict[str, Any]:
    if isinstance(event, HandStarted):
        return {
            "type": "hand_started",
            "hand_number": event.hand_number,
            "button": event.button,
            "stacks": list(event.stacks),
        }
    if isinstance(event, BlindPosted):
        return {
            "type": "blind_posted",
            "seat_id": event.seat_id,
            "amount": event.amount,
            "kind": event.kind.value,
            "is_all_in": event.is_all_in,
        }
    if isinstance(event, HoleDealt):
        return {"type": "hole_dealt", "seat_id": event.seat_id, "cards": _card_list(event.cards)}
    if isinstance(event, ActionRequested):
        return {"type": "action_requested", "seat_id": event.seat_id}
    if isinstance(event, PlayerActed):
        return {
            "type": "player_acted",
            "seat_id": event.seat_id,
            "action": _encode_action(event.action),
            "chips": event.chips,
            "stack": event.stack,
            "street_bet": event.street_bet,
        }
    if isinstance(event, StreetDealt):
        return {
            "type": "street_dealt",
            "street": event.street.value,
            "cards": _card_list(event.cards),
            "board": _card_list(event.board),
        }
    if isinstance(event, Showdown):
        return {
            "type": "showdown",
            "revelations": [
                {
                    "seat_id": hand.seat_id,
                    "hole": _card_list(hand.hole),
                    "score": _encode_score(hand.score),
                }
                for hand in event.revelations
            ],
        }
    if isinstance(event, PotsAwarded):
        return {
            "type": "pots_awarded",
            "awards": [
                {
                    "pot_index": award.pot_index,
                    "amount": award.amount,
                    "winners": list(award.winners),
                    "shares": list(award.shares),
                }
                for award in event.awards
            ],
        }
    if isinstance(event, PlayerBusted):
        return {"type": "player_busted", "seat_id": event.seat_id}
    if isinstance(event, TournamentEnded):
        return {"type": "tournament_ended", "winner": event.winner}
    if isinstance(event, HandEnded):
        return {"type": "hand_ended", "hand_number": event.hand_number}
    raise TypeError(f"unsupported event {type(event).__name__}")


def _decode_event(raw: Mapping[str, object]) -> Event:
    kind = _string(raw.get("type"), "event.type")
    if kind == "hand_started":
        return HandStarted(
            _integer(raw.get("hand_number"), "hand_number"),
            _integer(raw.get("button"), "button"),
            tuple(_integers(raw.get("stacks"), "stacks")),
        )
    if kind == "blind_posted":
        return BlindPosted(
            _integer(raw.get("seat_id"), "seat_id"),
            _integer(raw.get("amount"), "amount"),
            BlindKind(_string(raw.get("kind"), "kind")),
            _boolean(raw.get("is_all_in"), "is_all_in"),
        )
    if kind == "hole_dealt":
        cards = tuple(_cards(raw.get("cards"), "cards"))
        if len(cards) != 2:
            raise ProtocolError("hole_dealt requires two cards")
        return HoleDealt(_integer(raw.get("seat_id"), "seat_id"), (cards[0], cards[1]))
    if kind == "action_requested":
        return ActionRequested(_integer(raw.get("seat_id"), "seat_id"))
    if kind == "player_acted":
        return PlayerActed(
            _integer(raw.get("seat_id"), "seat_id"),
            _decode_action(_mapping(raw.get("action"), "action")),
            _integer(raw.get("chips"), "chips"),
            _integer(raw.get("stack"), "stack"),
            _integer(raw.get("street_bet"), "street_bet"),
        )
    if kind == "street_dealt":
        return StreetDealt(
            Street(_string(raw.get("street"), "street")),
            tuple(_cards(raw.get("cards"), "cards")),
            tuple(_cards(raw.get("board"), "board")),
        )
    if kind == "showdown":
        revelations: list[ShowdownHand] = []
        for item in _sequence(raw.get("revelations"), "revelations"):
            hand = _mapping(item, "showdown hand")
            hole = tuple(_cards(hand.get("hole"), "hole"))
            if len(hole) != 2:
                raise ProtocolError("showdown hand requires two hole cards")
            revelations.append(
                ShowdownHand(
                    _integer(hand.get("seat_id"), "seat_id"),
                    (hole[0], hole[1]),
                    _decode_score(_mapping(hand.get("score"), "score")),
                )
            )
        return Showdown(tuple(revelations))
    if kind == "pots_awarded":
        return PotsAwarded(
            tuple(
                PotAward(
                    _integer(award.get("pot_index"), "pot_index"),
                    _integer(award.get("amount"), "amount"),
                    tuple(_integers(award.get("winners"), "winners")),
                    tuple(_integers(award.get("shares"), "shares")),
                )
                for item in _sequence(raw.get("awards"), "awards")
                for award in [_mapping(item, "award")]
            )
        )
    if kind == "player_busted":
        return PlayerBusted(_integer(raw.get("seat_id"), "seat_id"))
    if kind == "tournament_ended":
        return TournamentEnded(_integer(raw.get("winner"), "winner"))
    if kind == "hand_ended":
        return HandEnded(_integer(raw.get("hand_number"), "hand_number"))
    raise ProtocolError(f"unknown event type {kind!r}")


def _encode_score(score: HandScore) -> dict[str, Any]:
    return {
        "rank": score.rank.value,
        "high_card_score": list(score.high_card_score),
        "cards": _card_list(score.cards),
    }


def _decode_score(raw: Mapping[str, object]) -> HandScore:
    return HandScore(
        HandRank(_integer(raw.get("rank"), "score.rank")),
        tuple(_integers(raw.get("high_card_score"), "score.high_card_score")),
        list(_cards(raw.get("cards"), "score.cards")),
    )


def _card(card: Card) -> str:
    return format_card(card)


def _card_list(cards: Sequence[Card]) -> list[str]:
    return [_card(card) for card in cards]


def _cards(value: object, name: str) -> list[Card]:
    return [parse_card(_string(card, name)) for card in _sequence(value, name)]


def _integers(value: object, name: str) -> list[int]:
    return [_integer(item, name) for item in _sequence(value, name)]


def _optional_int(value: object, name: str) -> int | None:
    return None if value is None else _integer(value, name)


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        _invalid(name, "object")
    return value


def _sequence(value: object, name: str) -> Sequence[object]:
    if not isinstance(value, list):
        _invalid(name, "array")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str):
        _invalid(name, "string")
    return value


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        _invalid(name, "integer")
    return value


def _boolean(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        _invalid(name, "boolean")
    return value


def _invalid(name: str, expected: str) -> NoReturn:
    raise ProtocolError(f"{name} must be a JSON {expected}")
