from textual.app import ComposeResult
from textual.widgets import Input, Label
from textual.validation import Function
from textual import on
from textual.containers import Horizontal


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
        yield Input(id=self.input_widget_id, classes="bottom-inputs")

    def focus(self) -> None:
        self.query_one(f"#{self.input_widget_id}").focus()

    def on_hide(self) -> None:
        self.query_one(f"#{self.input_widget_id}", Input).value = ""


class AddBox(EditBox):
    input_widget_id = "add-input"
    label_id = "add-label"

    def compose(self) -> ComposeResult:
        yield Label("Edit:", id=self.label_id, classes="bottom-labels")
        yield Input(
            id=self.input_widget_id,
            classes="bottom-inputs",
            validate_on=["submitted"],
            validators=[
                Function(contains_equals_sign, "Must contain '='"),
                Function(
                    not_only_whitespace, "The key or value can't be only whitespace!"
                ),
                Function(
                    no_comma,
                    "The key or value can't contain a comma! Only one key-value pair can be added at a time.",
                ),
            ],
        )

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


def contains_equals_sign(value: str) -> bool:
    return "=" in value


def not_only_whitespace(value: str) -> bool:
    for input in value.split("="):
        if not input.strip():
            return False
    return True


def no_comma(value: str) -> bool:
    return "," not in value
