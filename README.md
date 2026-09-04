# holdem

No-Limit Texas Hold'em written in Python. The goal is a correct, testable engine
that supports local play, bots, and peer-to-peer online sessions via
[Iroh](https://iroh.computer/).

## Status

| Phase | Description | State |
|-------|-------------|-------|
| 0 | Foundations – package layout, CI, tooling | ✅ done |
| 1 | Domain + engine + tests (Table, streets, side pots) | ✅ done |
| 2 | Actor protocol + bots | 🔲 next |
| 3 | Rich CLI (`holdem play`) | 🔲 planned |
| 4 | Iroh lobby (`holdem host` / `holdem join`) | 🔲 planned |

See [`holdem_rebuild_plan.md`](.cursor/plans/holdem_rebuild_plan_589543f9.plan.md) for the full design.

## Requirements

* Python ≥ 3.11
* [pip](https://pip.pypa.io/)

## Installation

```bash
git clone <repo-url>
cd poker-game
pip install -e ".[dev]"   # installs runtime + dev tools
```

## Usage

```text
holdem   # CLI not yet implemented (Phase 3)
```

## Development

```bash
make test        # run pytest with coverage
make lint        # ruff check + format
make typecheck   # mypy strict
make install     # pip install -e ".[dev]"
```

### Running tests directly

```bash
pytest           # uses settings from pyproject.toml
pytest -v tests/domain/test_hands.py   # just the hand-evaluation suite
```

## Project layout

```
src/holdem/
  domain/       # cards, hands, actions, events, seat views  – no I/O
  engine/       # Table state machine, betting, side pots, streets
  app/          # CLI composition root (Phase 3 stub)
tests/
  domain/       # hand evaluation + card codec
  engine/       # blinds, streets, actions, pots, showdown, replay
```

## Architecture (target)

```
holdem.domain   pure value types + hand evaluator
holdem.engine   Table state machine, betting, pots, streets   (done)
holdem.actors   Actor protocol, LocalHuman, RandomBot         (Phase 2)
holdem.ui.cli   Rich renderer + prompts                       (Phase 3)
holdem.connectors  InMemoryConnector, IrohConnector           (Phase 4)
holdem.app      play / host / join entry points               (Phase 3-4)
```

One rule: **the engine never touches I/O**. Bots, CLI, and Iroh are adapters.

## License

GNU General Public License v3.0 – see [LICENSE](LICENSE).
