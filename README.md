# holdem

No-Limit Texas Hold'em in Python. Play locally against bots now; peer-to-peer
sessions via [Iroh](https://iroh.computer/) come later.

Requires **Python 3.11+**.

## Play

```bash
git clone https://github.com/davidus27/poker-game.git
cd poker-game
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
holdem play
```

That opens a lobby: a welcome, your name, then a menu. Local play against bots
is ready now. Host and join are listed so the flow is in place; they explain
that online play lands later.

New local game shows the current table settings (6 players, 1000 chips, blinds
5/10) and asks if you want to change them. Press Enter to keep the defaults.

Each turn, pick a number from the legal-action menu. Hands keep going until
one stack remains. After the game you return to the menu. `Ctrl+C` cancels.

```bash
holdem                         # same lobby as holdem play
holdem play --name Dave
holdem play --players 3 --stack 500 --blinds 1/2
holdem host                    # placeholder until Iroh
holdem join TICKET             # placeholder until Iroh
holdem play --seed 42          # same deals every time
```

## Development

```bash
make install     # pip install -e ".[dev]"
make test        # pytest with coverage
make lint        # ruff check + format
make typecheck   # mypy strict
```

```bash
pytest                                      # settings from pyproject.toml
pytest -v tests/domain/test_hands.py        # hand-evaluation suite only
```

## Status

| Phase | Description                                         | State   |
| ----- | --------------------------------------------------- | ------- |
| 0     | Foundations – package layout, CI, tooling           | done    |
| 1     | Domain + engine + tests (Table, streets, side pots) | done    |
| 2     | Actor protocol + bots                               | done    |
| 3     | Rich CLI (`holdem play`)                            | done    |
| 4     | Iroh lobby (`holdem host` / `holdem join`)          | planned |

See the [rebuild plan](.cursor/plans/holdem_rebuild_plan_589543f9.plan.md) for the full design.

## Project layout

```
src/holdem/
  domain/       # cards, hands, actions, events, seat views  – no I/O
  engine/       # Table state machine, betting, side pots, streets
  actors/       # LocalHuman, RandomBot, and actor protocols
  ui/cli/       # Rich renderer and validated action/setup prompts
  app/          # CLI composition roots
tests/
  domain/       # hand evaluation + card codec
  engine/       # blinds, streets, actions, pots, showdown, replay
  actors/       # actor behavior
  ui/           # renderer and prompt tests
```

## Architecture

```
holdem.domain   pure value types + hand evaluator
holdem.engine   Table state machine, betting, pots, streets   (done)
holdem.actors   Actor protocol, LocalHuman, RandomBot         (done)
holdem.ui.cli   Rich renderer + prompts                       (done)
holdem.connectors  InMemoryConnector, IrohConnector           (Phase 4)
holdem.app      play / host / join entry points               (Phase 4 remaining)
```

One rule: **the engine never touches I/O**. Bots, CLI, and Iroh are adapters.

## License

GNU General Public License v3.0 – see [LICENSE](LICENSE).
