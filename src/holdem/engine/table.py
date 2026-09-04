"""Host-authoritative NL Hold'em table. Synchronous, I/O-free."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass, field

from holdem.domain.actions import Action, ActionKind
from holdem.domain.cards import Card
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
from holdem.domain.hands import find_best_hand
from holdem.domain.views import (
    LegalAction,
    PotView,
    PublicSeat,
    SeatStatus,
    SeatView,
    Street,
)
from holdem.engine.deck import Deck
from holdem.engine.exceptions import EngineStateError, IllegalAction
from holdem.engine.pots import build_pots, return_uncalled


@dataclass
class _Seat:
    seat_id: int
    stack: int
    hole: tuple[Card, Card] | None = None
    status: SeatStatus = SeatStatus.ACTIVE
    committed: int = 0
    street_bet: int = 0
    has_acted: bool = False


@dataclass
class Table:
    """Deterministic NL Hold'em state machine.

    Call :meth:`start_hand` to begin, then :meth:`apply` for each action
    from :attr:`to_act`. Query :meth:`seat_view` for a seat-private snapshot.
    """

    stacks: Sequence[int]
    small_blind: int = 5
    big_blind: int = 10
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        if len(self.stacks) < 2:
            raise ValueError("at least two seats are required")
        if self.small_blind <= 0 or self.big_blind <= 0:
            raise ValueError("blinds must be positive")
        if self.small_blind > self.big_blind:
            raise ValueError("small blind cannot exceed big blind")
        if any(stack < 0 for stack in self.stacks):
            raise ValueError("stacks cannot be negative")
        self._seats: list[_Seat] = [
            _Seat(seat_id=i, stack=stack) for i, stack in enumerate(self.stacks)
        ]
        for seat in self._seats:
            if seat.stack == 0:
                seat.status = SeatStatus.BUSTED
        self._button: int = self._first_live_seat()
        self._hand_number: int = 0
        self._street: Street = Street.WAITING
        self._board: list[Card] = []
        self._deck: Deck | None = None
        self._to_act: int | None = None
        self._current_bet: int = 0
        self._last_raise_size: int = self.big_blind
        self._sb_seat: int | None = None
        self._bb_seat: int | None = None

    # ------------------------------------------------------------------
    # Public queries
    # ------------------------------------------------------------------

    @property
    def to_act(self) -> int | None:
        return self._to_act

    @property
    def street(self) -> Street:
        return self._street

    @property
    def button(self) -> int:
        return self._button

    @property
    def board(self) -> tuple[Card, ...]:
        return tuple(self._board)

    @property
    def hand_number(self) -> int:
        return self._hand_number

    @property
    def is_hand_over(self) -> bool:
        return self._street in {Street.HAND_OVER, Street.TOURNAMENT_OVER, Street.WAITING}

    @property
    def is_tournament_over(self) -> bool:
        return self._street == Street.TOURNAMENT_OVER

    def stacks_now(self) -> tuple[int, ...]:
        return tuple(seat.stack for seat in self._seats)

    def seat_view(self, seat_id: int) -> SeatView:
        seat = self._require_seat(seat_id)
        hole: tuple[Card, ...] = seat.hole if seat.hole is not None else ()
        committed = {s.seat_id: s.committed for s in self._seats}
        folded = {s.seat_id for s in self._seats if s.status == SeatStatus.FOLDED}
        pots = tuple(
            PotView(amount=pot.amount, eligible=pot.eligible)
            for pot in build_pots(committed, folded)
        )
        legal: tuple[LegalAction, ...] = ()
        if self._to_act == seat_id:
            legal = self._legal_actions(seat)
        return SeatView(
            seat_id=seat_id,
            street=self._street,
            hand_number=self._hand_number,
            button=self._button,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            board=tuple(self._board),
            hole=hole,
            pot_total=sum(s.committed for s in self._seats),
            pots=pots,
            seats=tuple(
                PublicSeat(
                    seat_id=s.seat_id,
                    stack=s.stack,
                    status=s.status,
                    street_bet=s.street_bet,
                    committed=s.committed,
                )
                for s in self._seats
            ),
            to_act=self._to_act,
            legal_actions=legal,
            current_bet=self._current_bet,
            min_raise_to=self._min_raise_to(seat) if self._to_act == seat_id else None,
        )

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def start_hand(self, cards: Sequence[Card] | None = None) -> list[Event]:
        if self._street not in {Street.WAITING, Street.HAND_OVER}:
            if self._street == Street.TOURNAMENT_OVER:
                raise EngineStateError("tournament is over")
            raise EngineStateError("a hand is already in progress")
        live = self._live_seats()
        if len(live) < 2:
            raise EngineStateError("need at least two players with chips")

        if self._hand_number > 0:
            self._button = self._next_live(self._button)

        self._hand_number += 1
        self._board = []
        self._deck = Deck(list(cards) if cards is not None else None, rng=self.rng)
        self._street = Street.PREFLOP
        self._current_bet = 0
        self._last_raise_size = self.big_blind
        self._to_act = None

        for seat in self._seats:
            seat.hole = None
            seat.committed = 0
            seat.street_bet = 0
            seat.has_acted = False
            seat.status = SeatStatus.ACTIVE if seat.stack > 0 else SeatStatus.BUSTED

        events: list[Event] = [
            HandStarted(
                hand_number=self._hand_number,
                button=self._button,
                stacks=self.stacks_now(),
            )
        ]
        events.extend(self._post_blinds())
        events.extend(self._deal_holes())

        lone = self._one_remaining()
        if lone is not None:
            events.extend(self._finish_fold_win(lone))
            return events

        if self._betting_closed():
            events.extend(self._run_out_or_showdown())
            return events

        self._to_act = self._first_to_act_preflop()
        if self._to_act is None:
            events.extend(self._run_out_or_showdown())
            return events
        events.append(ActionRequested(self._to_act))
        return events

    def apply(self, action: Action) -> list[Event]:
        if self._to_act is None:
            raise IllegalAction("no player to act")
        seat = self._seats[self._to_act]
        if not self._action_is_legal(seat, action):
            raise IllegalAction(f"illegal action {action.kind.value} for seat {seat.seat_id}")

        chips = self._execute(seat, action)
        events: list[Event] = [
            PlayerActed(
                seat_id=seat.seat_id,
                action=action,
                chips=chips,
                stack=seat.stack,
                street_bet=seat.street_bet,
            )
        ]

        winner = self._one_remaining()
        if winner is not None:
            events.extend(self._finish_fold_win(winner))
            return events

        if self._street_betting_complete():
            events.extend(self._advance_street())
            return events

        self._to_act = self._next_actor(seat.seat_id)
        if self._to_act is None:
            events.extend(self._advance_street())
            return events
        events.append(ActionRequested(self._to_act))
        return events

    # ------------------------------------------------------------------
    # Blinds and dealing
    # ------------------------------------------------------------------

    def _post_blinds(self) -> list[Event]:
        live = self._live_seats()
        if len(live) == 2:
            sb = self._seats[self._button]
            bb = self._seats[self._other_live(self._button)]
        else:
            sb = self._seats[self._next_live(self._button)]
            bb = self._seats[self._next_live(sb.seat_id)]
        self._sb_seat = sb.seat_id
        self._bb_seat = bb.seat_id

        events: list[Event] = [
            self._post_blind(sb, self.small_blind, BlindKind.SMALL),
            self._post_blind(bb, self.big_blind, BlindKind.BIG),
        ]
        self._current_bet = max(s.street_bet for s in self._seats)
        return events

    def _post_blind(self, seat: _Seat, amount: int, kind: BlindKind) -> BlindPosted:
        posted = min(seat.stack, amount)
        seat.stack -= posted
        seat.street_bet += posted
        seat.committed += posted
        is_all_in = seat.stack == 0
        if is_all_in:
            seat.status = SeatStatus.ALL_IN
        return BlindPosted(seat_id=seat.seat_id, amount=posted, kind=kind, is_all_in=is_all_in)

    def _deal_holes(self) -> list[Event]:
        assert self._deck is not None
        live = [s for s in self._clockwise_from(self._button) if s.status != SeatStatus.BUSTED]
        first: list[Card] = []
        second: list[Card] = []
        for _ in live:
            first.append(self._deck.draw(1)[0])
        for _ in live:
            second.append(self._deck.draw(1)[0])
        events: list[Event] = []
        for seat, a, b in zip(live, first, second, strict=True):
            seat.hole = (a, b)
            events.append(HoleDealt(seat_id=seat.seat_id, cards=(a, b)))
        return events

    def _deal_board(self, street: Street, n: int) -> StreetDealt:
        assert self._deck is not None
        cards = tuple(self._deck.draw(n))
        self._board.extend(cards)
        return StreetDealt(street=street, cards=cards, board=tuple(self._board))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _legal_actions(self, seat: _Seat) -> tuple[LegalAction, ...]:
        if seat.status != SeatStatus.ACTIVE:
            return ()
        to_call = self._to_call(seat)
        actions: list[LegalAction] = []
        if to_call > 0:
            actions.append(LegalAction(ActionKind.FOLD))
            actions.append(LegalAction(ActionKind.CALL))
        else:
            actions.append(LegalAction(ActionKind.CHECK))

        min_to = self._min_raise_to(seat)
        max_to = seat.stack + seat.street_bet
        can_reopen = not seat.has_acted
        if can_reopen and seat.stack > to_call and min_to is not None and max_to >= min_to:
            actions.append(LegalAction(ActionKind.RAISE, min_amount=min_to, max_amount=max_to))

        if seat.stack > 0:
            actions.append(LegalAction(ActionKind.ALL_IN))
        return tuple(actions)

    def _action_is_legal(self, seat: _Seat, action: Action) -> bool:
        for legal in self._legal_actions(seat):
            if action.kind != legal.kind:
                continue
            if action.kind == ActionKind.RAISE:
                if action.amount is None or legal.min_amount is None or legal.max_amount is None:
                    return False
                return legal.min_amount <= action.amount <= legal.max_amount
            return True
        return False

    def _execute(self, seat: _Seat, action: Action) -> int:
        if action.kind == ActionKind.FOLD:
            seat.status = SeatStatus.FOLDED
            seat.has_acted = True
            return 0
        if action.kind == ActionKind.CHECK:
            seat.has_acted = True
            return 0
        if action.kind == ActionKind.CALL:
            return self._put_chips(seat, self._to_call(seat), is_raise=False)
        if action.kind == ActionKind.RAISE:
            assert action.amount is not None
            put = action.amount - seat.street_bet
            return self._put_chips(seat, put, is_raise=True)
        # ALL_IN
        put = seat.stack
        new_street = seat.street_bet + put
        return self._put_chips(seat, put, is_raise=new_street > self._current_bet)

    def _put_chips(self, seat: _Seat, amount: int, *, is_raise: bool) -> int:
        amount = min(amount, seat.stack)
        if amount < 0:
            amount = 0
        previous_bet = self._current_bet
        seat.stack -= amount
        seat.street_bet += amount
        seat.committed += amount
        seat.has_acted = True
        if seat.stack == 0:
            seat.status = SeatStatus.ALL_IN

        if is_raise and seat.street_bet > previous_bet:
            increment = seat.street_bet - previous_bet
            if increment >= self._last_raise_size:
                self._last_raise_size = increment
                self._reopen_others(seat.seat_id)
            self._current_bet = seat.street_bet
        elif seat.street_bet > self._current_bet:
            # short all-in that increased the bet without a full raise
            self._current_bet = seat.street_bet
        return amount

    def _reopen_others(self, aggressor: int) -> None:
        for seat in self._seats:
            if seat.seat_id != aggressor and seat.status == SeatStatus.ACTIVE:
                seat.has_acted = False

    def _to_call(self, seat: _Seat) -> int:
        return max(0, self._current_bet - seat.street_bet)

    def _min_raise_to(self, seat: _Seat) -> int | None:
        if seat.status != SeatStatus.ACTIVE:
            return None
        if seat.has_acted:
            return None
        to_call = self._to_call(seat)
        if seat.stack <= to_call:
            return None
        target = self._current_bet + self._last_raise_size
        if self._current_bet == 0:
            target = self.big_blind
        max_to = seat.stack + seat.street_bet
        if max_to < target:
            return None
        return target

    # ------------------------------------------------------------------
    # Street progression
    # ------------------------------------------------------------------

    def _street_betting_complete(self) -> bool:
        active = self._active_seats()
        if not active:
            return True
        if any(seat.street_bet < self._current_bet for seat in active):
            return False
        return all(seat.has_acted for seat in active)

    def _betting_closed(self) -> bool:
        active = self._active_seats()
        if len(active) == 0:
            return True
        if len(active) == 1 and active[0].street_bet >= self._current_bet:
            return True
        return False

    def _advance_street(self) -> list[Event]:
        if self._street == Street.RIVER:
            return self._finish_showdown()
        return self._run_out_or_showdown(stop_for_betting=True)

    def _run_out_or_showdown(self, *, stop_for_betting: bool = False) -> list[Event]:
        events: list[Event] = []
        while True:
            if self._street == Street.PREFLOP:
                events.append(self._deal_board(Street.FLOP, 3))
                self._street = Street.FLOP
            elif self._street == Street.FLOP:
                events.append(self._deal_board(Street.TURN, 1))
                self._street = Street.TURN
            elif self._street == Street.TURN:
                events.append(self._deal_board(Street.RIVER, 1))
                self._street = Street.RIVER
            elif self._street == Street.RIVER:
                events.extend(self._finish_showdown())
                return events
            else:
                raise EngineStateError(f"cannot advance from {self._street}")

            self._reset_street()
            if not stop_for_betting or self._betting_closed():
                continue
            self._to_act = self._first_to_act_postflop()
            if self._to_act is None:
                continue
            events.append(ActionRequested(self._to_act))
            return events

    def _reset_street(self) -> None:
        self._current_bet = 0
        self._last_raise_size = self.big_blind
        self._to_act = None
        for seat in self._seats:
            seat.street_bet = 0
            seat.has_acted = False

    def _first_to_act_preflop(self) -> int | None:
        assert self._bb_seat is not None
        return self._next_actor(self._bb_seat)

    def _first_to_act_postflop(self) -> int | None:
        return self._next_actor(self._button)

    def _next_actor(self, after: int) -> int | None:
        for seat in self._clockwise_from(after):
            if seat.status == SeatStatus.ACTIVE:
                if seat.street_bet < self._current_bet or not seat.has_acted:
                    return seat.seat_id
        return None

    # ------------------------------------------------------------------
    # Showdown and awards
    # ------------------------------------------------------------------

    def _finish_fold_win(self, winner: _Seat) -> list[Event]:
        return self._award_and_close(showdown=None, remaining={winner.seat_id})

    def _finish_showdown(self) -> list[Event]:
        self._street = Street.SHOWDOWN
        remaining = [
            s for s in self._seats if s.status in {SeatStatus.ACTIVE, SeatStatus.ALL_IN} and s.hole
        ]
        revelations = []
        for seat in remaining:
            assert seat.hole is not None
            score = find_best_hand(list(self._board), list(seat.hole))
            revelations.append(ShowdownHand(seat_id=seat.seat_id, hole=seat.hole, score=score))
        showdown = Showdown(revelations=tuple(revelations))
        return self._award_and_close(
            showdown=showdown,
            remaining={s.seat_id for s in remaining},
        )

    def _award_and_close(self, showdown: Showdown | None, remaining: set[int]) -> list[Event]:
        events: list[Event] = []
        if showdown is not None:
            events.append(showdown)

        committed = {s.seat_id: s.committed for s in self._seats}
        adjusted = return_uncalled(committed)
        for seat in self._seats:
            refund = committed[seat.seat_id] - adjusted[seat.seat_id]
            if refund:
                seat.stack += refund
                seat.committed -= refund

        folded = {s.seat_id for s in self._seats if s.seat_id not in remaining}
        pots = build_pots({s.seat_id: s.committed for s in self._seats}, folded)
        scores = {rev.seat_id: rev.score for rev in showdown.revelations} if showdown else {}

        awards: list[PotAward] = []
        for index, pot in enumerate(pots):
            eligible = [sid for sid in pot.eligible if sid in remaining]
            if not eligible:
                eligible = sorted(remaining)
            if showdown is None:
                winners = sorted(eligible)
            else:
                best = max(scores[sid] for sid in eligible)
                winners = [sid for sid in eligible if scores[sid] == best]
                winners = self._order_from_button(winners)
            share, leftover = divmod(pot.amount, len(winners))
            shares: list[int] = []
            for i, winner in enumerate(winners):
                extra = 1 if i < leftover else 0
                chunk = share + extra
                shares.append(chunk)
                self._seats[winner].stack += chunk
            awards.append(
                PotAward(
                    pot_index=index,
                    amount=pot.amount,
                    winners=tuple(winners),
                    shares=tuple(shares),
                )
            )
        events.append(PotsAwarded(awards=tuple(awards)))

        for seat in self._seats:
            if seat.status != SeatStatus.BUSTED and seat.stack == 0:
                seat.status = SeatStatus.BUSTED
                events.append(PlayerBusted(seat.seat_id))

        events.append(HandEnded(self._hand_number))
        self._to_act = None
        self._street = Street.HAND_OVER

        live = self._live_seats()
        if len(live) <= 1:
            self._street = Street.TOURNAMENT_OVER
            if live:
                events.append(TournamentEnded(winner=live[0].seat_id))
            else:
                # all stacks zero after a split that emptied everyone — should not happen
                events.append(TournamentEnded(winner=remaining.pop() if remaining else 0))
        return events

    def _order_from_button(self, seat_ids: list[int]) -> list[int]:
        order = [s.seat_id for s in self._clockwise_from(self._button)]
        return sorted(seat_ids, key=order.index)

    # ------------------------------------------------------------------
    # Seat helpers
    # ------------------------------------------------------------------

    def _require_seat(self, seat_id: int) -> _Seat:
        if seat_id < 0 or seat_id >= len(self._seats):
            raise ValueError(f"unknown seat {seat_id}")
        return self._seats[seat_id]

    def _live_seats(self) -> list[_Seat]:
        return [s for s in self._seats if s.stack > 0]

    def _active_seats(self) -> list[_Seat]:
        return [s for s in self._seats if s.status == SeatStatus.ACTIVE]

    def _in_hand(self) -> list[_Seat]:
        return [s for s in self._seats if s.status in {SeatStatus.ACTIVE, SeatStatus.ALL_IN}]

    def _one_remaining(self) -> _Seat | None:
        remaining = self._in_hand()
        if len(remaining) == 1:
            return remaining[0]
        return None

    def _first_live_seat(self) -> int:
        for seat in self._seats:
            if seat.stack > 0:
                return seat.seat_id
        raise EngineStateError("no live seats")

    def _next_live(self, after: int) -> int:
        for seat in self._clockwise_from(after):
            if seat.stack > 0:
                return seat.seat_id
        raise EngineStateError("no live seat after button")

    def _other_live(self, seat_id: int) -> int:
        for seat in self._seats:
            if seat.seat_id != seat_id and seat.stack > 0:
                return seat.seat_id
        raise EngineStateError("no opposing live seat")

    def _clockwise_from(self, after: int) -> list[_Seat]:
        n = len(self._seats)
        return [self._seats[(after + 1 + i) % n] for i in range(n)]
