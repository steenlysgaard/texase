from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label

from texase.formatting import (
    convert_str_to_other_type,
    convert_value_to_int_float_or_bool,
    correctly_typed_kvp,
    kvp_exception,
)
from texase.validators import kvp_validators_add, kvp_validators_edit


class InputScreen(ModalScreen[Any]):
    """Screen with an Input widget."""

    DEFAULT_CSS = """
        InputScreen {
            align: center middle;
        }

        InputScreen > Vertical {
            height: auto;
            content-align: center middle;
        }

        InputScreen > Vertical > Horizontal {
            height: auto;
        }

        #title-label-input-screen {
            text-align: center;
            width: 50%;
            height: auto;
            border: heavy $warning;
            padding: 2 4;
        }

        #input-input-screen {
            border-left: none;
            width: 1fr;
            padding: 0 1 0 0;
        }

        #key-label-input-screen{
            padding: 0 0 0 1;
            background: $boost;
            color: $text;
            width: auto;
            border: tall $accent;
            border-right: none;
        }
    """

    BINDINGS = [
        Binding("ctrl+g", "cancel", "Cancel"),
    ]

    validators = []

    def __init__(
        self, input_title: str, key: str = "", prefilled_input: str | None = None
    ) -> None:
        self.input_title = input_title
        self.prefilled_input = prefilled_input
        self.key = key
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            with Center():
                yield Label(self.input_title, id="title-label-input-screen")
            with Horizontal():
                key_label = self.key
                if key_label != "":
                    key_label += " = "
                yield Label(key_label, id="key-label-input-screen")
                yield Input(
                    value=self.prefilled_input,
                    id="input-input-screen",
                    validators=self.validators,
                    validate_on=["submitted"],
                )
        yield Footer()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        if (
            submitted.validation_result is not None
            and not submitted.validation_result.is_valid
        ):
            self.app.notify_error(
                "\n".join(submitted.validation_result.failure_descriptions),
                error_title="Invalid input",
            )
            # If not valid input stop bubbling further
            submitted.stop()
            return

        self.further_process_submitted(submitted)

    def further_process_submitted(self, submitted: Input.Submitted) -> None:
        raise NotImplementedError("Subclasses must implement this method.")


class KVPScreen(InputScreen):
    """Screen for adding a key value pair."""

    validators = kvp_validators_add

    def further_process_submitted(self, submitted: Input.Submitted) -> None:
        key, value = correctly_typed_kvp(submitted.value)

        exception_from_kvp = kvp_exception(key, value)
        if exception_from_kvp is not None:
            self.app.notify_error(exception_from_kvp, "ValueError")
            return

        self.dismiss((key, value))


class KVPEditScreen(InputScreen):
    """Screen for editing a key value pair."""

    validators = kvp_validators_edit

    def further_process_submitted(self, submitted: Input.Submitted) -> None:
        value = convert_value_to_int_float_or_bool(submitted.value)

        exception_from_kvp = kvp_exception(self.key, value)
        if exception_from_kvp is not None:
            self.app.notify_error(exception_from_kvp, "ValueError")
            return

        self.dismiss(value)


class DataScreen(InputScreen):
    """Screen for adding data."""

    def further_process_submitted(self, submitted: Input.Submitted) -> None:
        value = submitted.value.strip()
        key, data = value.split("=")
        self.dismiss((key, convert_str_to_other_type(data)))


class DataEditScreen(InputScreen):
    """Screen for editing data."""

    def further_process_submitted(self, submitted: Input.Submitted) -> None:
        data = submitted.value.strip()
        self.dismiss(convert_str_to_other_type(data))
