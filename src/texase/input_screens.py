from __future__ import annotations

from typing import Any, Tuple

from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, Input
from textual.binding import Binding
from textual.app import ComposeResult

from texase.validators import kvp_validators_add, kvp_validators_edit


class InputScreen(ModalScreen[Tuple[str, Any] | None]):
    """Screen with a question that can be answered yes or no."""

    DEFAULT_CSS = """
        InputScreen {
            align: center middle;
        }

        InputScreen > Label {
            text-align: center;
            width: 50%;
            height: auto;
            border: heavy $warning;
            padding: 2 4;
        }
"""

    BINDINGS = [
        Binding("ctrl+g", "cancel", "Cancel"),
    ]

    validators = []

    def __init__(self, text: Text, prefilled_input: str | None = None) -> None:
        self.text = text
        self.prefilled_input = prefilled_input
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label(self.text)
        yield Input(
            value=self.prefilled_input,
            id="input-kvpscreen",
            validators=self.validators,
            validate_on=["submitted"],
        )
        yield Footer()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, value: str) -> None:
        self.dismiss(value)

class KVPScreen(InputScreen):
    """Screen for adding a key value pair."""

    validators = kvp_validators_add

    def on_input_submitted(self, value: str) -> None:
        self.dismiss(("key", value))
        
class DataScreen(InputScreen):
    """Screen for adding or editing data."""

    def on_input_submitted(self, value: str) -> None:
        value = value.strip()
        value.split("=")
        self.dismiss(("data", value))
