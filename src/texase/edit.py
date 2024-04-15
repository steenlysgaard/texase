from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.validation import Function
from textual.widgets import Input, Label

from texase.validators import kvp_validators_add, kvp_validators_edit


class EditBox(Horizontal):
    BINDINGS = [
        # Hiding boxes shortcut is already defined in app, just
        # redefining the binding here to make it show in the edit
        # box
        ("ctrl+g", "hide_edit", "Undo/Hide"),
    ]

    input_widget_id = "edit-input"
    label_id = "edit-label"

    def compose(self) -> ComposeResult:
        yield Label("Edit:", id=self.label_id, classes="bottom-labels")
        yield Input(
            id=self.input_widget_id,
            classes="bottom-inputs",
            validators=kvp_validators_edit,
            validate_on=["submitted"],
        )

    def focus(self) -> None:
        self.query_one(f"#{self.input_widget_id}").focus()

    def on_hide(self) -> None:
        self.query_one(f"#{self.input_widget_id}", Input).value = ""

    @on(Input.Submitted)
    def show_invalid_reasons(self, event: Input.Submitted) -> None:
        # Updating the UI to show the reasons why validation failed
        if not event.validation_result.is_valid:
            self.query_one(f"#{self.label_id}").add_class("-invalid")
            self.notify(
                "\n".join(event.validation_result.failure_descriptions),
                title="Invalid input",
                severity="error",
            )
        else:
            self.query_one(f"#{self.label_id}").remove_class("-invalid")

class AddBox(EditBox):
    input_widget_id = "add-input"
    label_id = "add-label"

    def compose(self) -> ComposeResult:
        yield Label("Edit:", id=self.label_id, classes="bottom-labels")
        yield Input(
            id=self.input_widget_id,
            classes="bottom-inputs",
            validate_on=["submitted"],
            validators=kvp_validators_add,
        )

