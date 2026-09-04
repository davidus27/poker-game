"""Command-line entry point."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from rich.console import Console

from holdem.actors import BotDifficulty
from holdem.app.lobby import run_lobby
from holdem.ui.cli.lobby import MenuOption
from holdem.ui.cli.prompts import (
    DEFAULT_BIG_BLIND,
    DEFAULT_PLAYERS,
    DEFAULT_SMALL_BLIND,
    DEFAULT_STARTING_STACK,
    PlayConfig,
    parse_blinds,
)


def _blinds_arg(raw: str) -> tuple[int, int]:
    try:
        return parse_blinds(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _session_flags() -> argparse.ArgumentParser:
    flags = argparse.ArgumentParser(add_help=False)
    flags.add_argument("--seed", type=int, help="seed the game for a repeatable deal")
    flags.add_argument("--name", help="display name at the table (default: You)")
    flags.add_argument(
        "--players",
        "--seats",
        dest="players",
        type=int,
        metavar="N",
        help=f"seats including you (default: {DEFAULT_PLAYERS})",
    )
    flags.add_argument(
        "--stack",
        type=int,
        metavar="CHIPS",
        help=f"starting chips per seat (default: {DEFAULT_STARTING_STACK})",
    )
    flags.add_argument(
        "--blinds",
        type=_blinds_arg,
        metavar="SMALL/BIG",
        help=f"blinds (default: {DEFAULT_SMALL_BLIND}/{DEFAULT_BIG_BLIND})",
    )
    flags.add_argument(
        "--bots",
        type=int,
        metavar="N",
        help="bot seats on hosted tables (default: 0)",
    )
    flags.add_argument(
        "--difficulty",
        type=BotDifficulty,
        choices=BotDifficulty,
        metavar="LEVEL",
        help="bot difficulty for local and hosted tables: easy, medium, or hard (default: medium)",
    )
    return flags


def build_parser() -> argparse.ArgumentParser:
    session = _session_flags()
    parser = argparse.ArgumentParser(
        prog="holdem",
        description="No-Limit Texas Hold'em",
        parents=[session],
    )
    commands = parser.add_subparsers(dest="command", required=False)
    commands.add_parser("play", parents=[session], help="open the lobby and play locally")
    commands.add_parser(
        "host",
        parents=[session],
        help="host an online table and print an Iroh ticket",
    )
    join = commands.add_parser(
        "join",
        parents=[session],
        help="join an online table with an Iroh ticket",
    )
    join.add_argument("ticket", nargs="?", help="table ticket from the host")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()
    try:
        config = PlayConfig.from_options(
            players=args.players,
            starting_stack=args.stack,
            blinds=args.blinds,
            seed=args.seed,
            bots=args.bots,
            difficulty=args.difficulty,
        )
    except ValueError as exc:
        parser.error(str(exc))

    opening = {
        "host": MenuOption.HOST,
        "join": MenuOption.JOIN,
    }.get(args.command)
    ticket = getattr(args, "ticket", None)

    try:
        run_lobby(
            console=console,
            table=config,
            display_name=args.name,
            opening=opening,
            join_ticket=ticket,
        )
    except (EOFError, KeyboardInterrupt):
        console.print("\nSee you at the table.")
