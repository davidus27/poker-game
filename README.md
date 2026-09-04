# holdem

No-Limit Texas Hold'em in Python. Play locally against bots or host a
peer-to-peer table via [Iroh](https://iroh.computer/).

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

For online play, install the optional Iroh binding:

```bash
pip install -e ".[network]"
```

The lobby supports local play, hosting, and joining. The host runs the
authoritative game engine; guests receive only their seat-private snapshots.

New local game shows the current table settings (6 players, 1000 chips, blinds
5/10) and asks if you want to change them. Press Enter to keep the defaults.

Each turn, pick a number from the legal-action menu. Hands keep going until
one stack remains. After the game you return to the menu. `Ctrl+C` cancels.

```bash
holdem                         # same lobby as holdem play
holdem play --name Dave
holdem play --players 3 --stack 500 --blinds 1/2
holdem host --seats 2          # prints a ticket to share
holdem join TICKET             # connect to the host
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



## Project layout

```
src/holdem/
  domain/       # cards, hands, actions, events, seat views  – no I/O
  engine/       # Table state machine, betting, side pots, streets
  actors/       # LocalHuman, RandomBot, and actor protocols
  protocol/     # Versioned JSON envelopes and private event filtering
  connectors/   # In-memory test transport and Iroh adapter
  ui/cli/       # Rich renderer and validated action/setup prompts
  app/          # Local, host, and guest composition roots
tests/
  domain/       # hand evaluation + card codec
  engine/       # blinds, streets, actions, pots, showdown, replay
  actors/       # actor behavior
  ui/           # renderer and prompt tests
  protocol/     # envelope round trips and privacy
  connectors/   # transport contract tests
```

## License

GNU General Public License v3.0 – see [LICENSE](LICENSE).