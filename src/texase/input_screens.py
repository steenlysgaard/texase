from __future__ import annotations

from typing import Any, Tuple

from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, Input
from textual.binding import Binding
from textual.app import ComposeResult

from texase.validators import kvp_validators_add, kvp_validators_edit
from texase.formatting import convert_str_to_other_type, correctly_typed_kvp, kvp_exception


class InputScreen(ModalScreen[Any]):
    """Screen with an Input widget."""

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

    def __init__(self, text: str, prefilled_input: str | None = None) -> None:
        self.text = text
        self.prefilled_input = prefilled_input
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label(self.text)
        yield Input(
            value=self.prefilled_input,
            id="input-inputscreen",
            validators=self.validators,
            validate_on=["submitted"],
        )
        yield Footer()

    def action_cancel(self) -> None:
        self.dismiss(None)

class KVPScreen(InputScreen):
    """Screen for adding a key value pair."""

    validators = kvp_validators_add

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        if submitted.validation_result is not None and not submitted.validation_result.is_valid:
            self.app.notify_error("\n".join(submitted.validation_result.failure_descriptions),
                                  error_title="Invalid input",)
            # If not valid input stop bubbling further
            submitted.stop()
            return
        
        key, value = correctly_typed_kvp(submitted.value)

        exception_from_kvp = kvp_exception(key, value)
        if exception_from_kvp is not None:
            self.app.notify_error(exception_from_kvp, "ValueError")
            return
        
        self.dismiss((key, value))
        
class DataScreen(InputScreen):
    """Screen for adding or editing data."""

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        if submitted.validation_result is not None and not submitted.validation_result.is_valid:
            self.app.notify_error("\n".join(submitted.validation_result.failure_descriptions),
                                  error_title="Invalid input",)
            # If not valid input stop bubbling further
            submitted.stop()
            return
        value = submitted.value.strip()
        key, data = value.split("=")
        self.dismiss((key, convert_str_to_other_type(data)))
