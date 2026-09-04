"""Shared Texas Hold'em banner for the lobby and the table."""

from __future__ import annotations

from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text

LOGO_TITLE = "TEXAS HOLD'EM"


def logo_mark() -> Text:
    """Compact suit-flanked title used on every screen."""

    mark = Text()
    mark.append("♠ ", style="bold white")
    mark.append("♥  ", style="bold red")
    mark.append(LOGO_TITLE, style="bold gold1")
    mark.append("  ♦", style="bold red")
    mark.append(" ♣", style="bold white")
    return mark


def logo_banner(*, subtitle: str | None = None) -> RenderableType:
    """Panel version of the mark, for the lobby and other full screens."""

    body = Text()
    body.append_text(logo_mark())
    if subtitle:
        body.append("\n")
        body.append(subtitle, style="dim")
    return Panel(Align.center(body), border_style="gold1")
