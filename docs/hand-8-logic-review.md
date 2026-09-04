# Hand 8 logic review

Reconstructed from the live CLI session (heads-up vs Bot 1; seats 2–5 already busted). Chip math and the showdown winner are correct. Several presentation bugs make the hand harder to read, and the evaluator has a real comparison bug that did **not** decide this pot.

## What actually happened

Opening chips (behind + already posted):

| Seat   | Behind | Posted | Start of hand |
| ------ | -----: | -----: | ------------: |
| You    |  3,880 | BB 10  |         3,890 |
| Bot 1  |  2,105 | SB 5   |         2,110 |
| Total  |        |        |         6,000 |

Heads-up blinds were right: Bot 1 had the button, posted the small blind, and acted first preflop. You were the big blind and acted first on every street after the flop.

| Street  | Action |
| ------- | ------ |
| Preflop | Bot 1 raises to 2,079 (31 behind). You call 2,069. Pot **4,158**. |
| Flop    | `3♥ 2♦ 8♣`. You check. Bot 1 checks. |
| Turn    | `5♦`. You check. Bot 1 bets 12. You call. Pot **4,182**. |
| River   | `Q♦`. You check. Bot 1 bets 10. You raise to 20. Bot 1 all-in for 19. |

Uncalled 1 chip from the river raise is returned. Pot **4,220** is awarded to you. Final stacks 6,000 / 0. Conservation holds.

Hole cards at showdown:

- **You** `2♥ 10♥` + board → **one pair, twos** (2♥ 2♦), kickers Q♦ 10♥ 8♣
- **Bot 1** `J♥ 4♥` + board → **queen-high** (Q♦ J♥ 8♣ 5♦ 4♥)

Pair beats high card. You should win this pot. The engine got the winner right.

---

## Problems

### 1. Showdown never says *why* anyone won (this session)

The log was:

```text
Showdown: You 2♥ 10♥, Bot 1 J♥ 4♥.
Pot awarded: 4,220 to You.
You wins the game!
```

`ShowdownHand` already carries a `HandScore` (`PAIR` vs `HIGH_CARD` plus the made five). The UI prints hole cards only. A player cannot tell this was pair-of-twos versus queen-high without doing the work by hand.

### 2. English is conjugated as if "You" were a third person

Throughout: "You posts", "You calls", "You checks", "You raises", "You wins". Should be post / call / check / raise / win. Bots are fine in the third person.

### 3. Pot breakdown treats unmatched chips as side pots

`seat_view` always runs `build_pots` on live committed amounts. Unequal commitments become extra layers even while the betting round is still open:

- After blinds only: `Pot 15  (10 · 5)` — looks like two pots; it is just SB 5 + BB 10.
- After Bot 1 raises to 2,079 and before you call: `Pot 2,089  (20 · 2,069)` — looks like a 2,069 side pot; you can still call and merge it.
- After you raise river to 20 vs a 10 bet: `Pot 4,212  (4,202 · 10)` — same thing, unmatched raise.

Real side pots (unequal all-ins that can no longer be matched) are a Hold'em rule. Showing them on every unmatched bet is misleading, not a mis-award. The final 4,220 award matches the rules.

### 4. "Last" column is not per-street

On the flop, Bot 1's Last still said `raises to 2,079` while Bet was 0. That was the **preflop** raise. Easy to read as a live bet. Last should reset (or be labeled) when the street changes.

### 5. Latest log is noisy and repeats itself

The same fact appears as the yellow headline and again in the dim history. `Waiting for Bot 1` is also logged even when the table already shows `→` and `thinking…`. After the win, `You wins the game!` is printed twice.

### 6. Opening a street is labeled "Raise"

On the flop, first to act, no bet yet: `Raise to 10–1811`. That is a **bet** (min = big blind). "Raise" should only appear when facing a bet. The amounts themselves (min 10, max stack) were legal.

### 7. Tournament-over frame still shows a street bet

After the award, You have stack 6,000 and Bet 20. The 20 is leftover street-bet UI; those chips are already in the 6,000. Harmless, confusing.

### 8. Busted seats stay in the table for the rest of the match

Not a rules error. Four `Busted` rows with `—` drown the heads-up that is actually playing.

### 9. Latent evaluator bug (did not affect this pot)

Hand categories are compared first (`PAIR` > `HIGH_CARD`), so this pot is safe.

Tie-breakers inside the same category use `get_high_card_score(chosen)`, which sorts **all** chosen ranks descending. For a pair, the pair rank is not forced to the front. Confirmed:

- Pair of twos with A-K-Q kickers **beats** pair of kings with 9-8-7 kickers.
- Three twos with A-K kickers **beats** three threes with low kickers.

Same-rank showdowns (pair vs pair, trips vs trips, …) can award the pot to the worse hand. Tests only compare kickers when the pair/trips rank is already an ace, so they never catch this.

---

## Not bugs

- RandomBot shoving ~2,079 preflop with J♥ 4♥ is legal; it is a random legal-action sampler, not a strategy bug.
- Min-raise to 20 on the river (facing 10) is the right minimum.
- All-in for 19 into 20, 1 chip uncalled, pot 4,220, is correct.
- HU action order (SB first preflop, BB first postflop) is correct.
