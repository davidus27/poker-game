"""Interactive and scripted terminal input helpers."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from typing import TypeVar, cast

import questionary
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent, merge_key_bindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from rich.console import Console

LineReader = Callable[[str], str]
T = TypeVar("T")

_BACK = object()
_HINT = "↑↓ to choose · Enter to confirm · Ctrl+C to go back"
_STYLE = Style.from_dict(
    {
        "highlighted": "fg:ansicyan bold",
        "pointer": "fg:ansicyan bold",
        "instruction": "fg:ansibrightblack",
    }
)


class Cancelled(Exception):
    """Raised when the user cancels the current prompt."""


class Prompter:
    """Use rich TTY prompts while retaining a deterministic line-input mode."""

    def __init__(
        self,
        *,
        reader: LineReader = input,
        console: Console | None = None,
    ) -> None:
        self.reader = reader
        self.console = console or Console()
        self.interactive = reader is input and sys.stdin.isatty()

    def select(
        self,
        title: str,
        choices: Sequence[tuple[str, T]],
        *,
        allow_back: bool = False,
    ) -> T:
        """Choose one labelled value, using arrows on a TTY and numbers otherwise."""

        if not choices:
            raise ValueError("select requires at least one choice")
        if self.interactive:
            return self._interactive_select(title, choices, allow_back=allow_back)
        return self._line_select(title, choices, allow_back=allow_back)

    def confirm(
        self,
        title: str,
        *,
        default: bool = False,
        allow_back: bool = False,
    ) -> bool:
        """Ask a yes/no question."""

        if self.interactive:
            answer = self._ask(
                questionary.confirm(
                    title,
                    default=default,
                    style=_STYLE,
                    instruction=_HINT if allow_back else None,
                )
            )
            if answer is None:
                raise Cancelled
            return bool(answer)

        hint = "Y/n" if default else "y/N"
        while True:
            raw = self._read(f"{title} [{hint}]: ").strip().lower()
            if not raw:
                return default
            if allow_back and raw in {"b", "back"}:
                raise Cancelled
            if raw in {"y", "yes"}:
                return True
            if raw in {"n", "no"}:
                return False
            self.console.print("[red]Enter y or n.[/red]")

    def ask_text(
        self,
        title: str,
        *,
        default: str = "",
        allow_back: bool = False,
    ) -> str:
        """Read text, optionally treating an empty answer as Back."""

        if self.interactive:
            answer = self._ask(
                questionary.text(
                    title,
                    default=default,
                    style=_STYLE,
                    instruction=_HINT if allow_back else None,
                )
            )
        else:
            suffix = f" [{default}]" if default else ""
            answer = self._read(f"{title}{suffix}: ").strip()
            if not answer:
                answer = default

        if answer is None or (
            allow_back and (not answer or str(answer).strip().lower() in {"b", "back"})
        ):
            raise Cancelled
        return str(answer)

    def ask_int(
        self,
        title: str,
        *,
        minimum: int,
        maximum: int | None = None,
        default: int | None = None,
        allow_back: bool = False,
    ) -> int:
        """Read and validate a whole number."""

        while True:
            raw = self.ask_text(
                title,
                default="" if default is None else str(default),
                allow_back=allow_back,
            )
            try:
                value = int(raw)
            except ValueError:
                self.console.print("[red]Enter a whole number.[/red]")
                continue
            if value < minimum or (maximum is not None and value > maximum):
                bounds = f"{minimum}–{maximum}" if maximum is not None else f"at least {minimum}"
                self.console.print(f"[red]Enter a value in the range {bounds}.[/red]")
                continue
            return value

    def pause(self, title: str = "Press Enter to continue: ") -> None:
        """Wait for acknowledgement, converting an interrupt into cancellation."""

        if self.interactive:
            answer = self._ask(
                questionary.press_any_key_to_continue(
                    title,
                    style=_STYLE,
                )
            )
            if answer is None:
                raise Cancelled
            return
        self._read(title)

    def _interactive_select(
        self,
        title: str,
        choices: Sequence[tuple[str, T]],
        *,
        allow_back: bool,
    ) -> T:
        rendered = [
            questionary.Choice(label, value=value, shortcut_key=str(index))
            for index, (label, value) in enumerate(choices, start=1)
            if index <= 9
        ]
        rendered.extend(
            questionary.Choice(label, value=value) for label, value in choices[len(rendered) :]
        )
        if allow_back:
            rendered.append(questionary.Choice("Back", value=_BACK))

        answer = self._ask(
            questionary.select(
                title,
                choices=rendered,
                pointer="❯",
                instruction=_HINT,
                style=_STYLE,
                use_shortcuts=True,
            )
        )
        if answer is None or answer is _BACK:
            raise Cancelled
        return cast(T, answer)

    def _line_select(
        self,
        title: str,
        choices: Sequence[tuple[str, T]],
        *,
        allow_back: bool,
    ) -> T:
        self.console.print(title)
        for index, (label, _value) in enumerate(choices, start=1):
            self.console.print(f"  [cyan]{index}[/cyan]. {label}")
        back_index = len(choices) + 1
        if allow_back:
            self.console.print(f"  [cyan]{back_index}[/cyan]. Back")

        while True:
            raw = self._read("Choose: ").strip().lower()
            if allow_back and raw in {"", "b", "back", str(back_index)}:
                raise Cancelled
            try:
                index = int(raw)
                if 1 <= index <= len(choices):
                    return choices[index - 1][1]
            except ValueError:
                pass
            self.console.print("[red]Choose one of the listed numbers.[/red]")

    def _read(self, prompt: str) -> str:
        try:
            return self.reader(prompt)
        except KeyboardInterrupt as exc:
            raise Cancelled from exc

    @staticmethod
    def _ask(question: questionary.Question) -> object:
        escape_binding = KeyBindings()

        @escape_binding.add(Keys.Escape, eager=True)
        def cancel(event: KeyPressEvent) -> None:
            event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

        existing_bindings = question.application.key_bindings
        if existing_bindings is None:
            question.application.key_bindings = escape_binding
        else:
            question.application.key_bindings = merge_key_bindings(
                [existing_bindings, escape_binding]
            )
        try:
            return question.unsafe_ask()
        except KeyboardInterrupt as exc:
            raise Cancelled from exc
