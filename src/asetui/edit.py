from textual.app import ComposeResult
from textual.widgets import Input, Label
from textual.containers import Horizontal

class EditBox(Horizontal):
    BINDINGS = [
        # Hiding boxes shortcut is already defined in app, just
        # redefining the binding here to make it show in the edit
        # box
        ("ctrl+g", "hide_edit", "Undo/Hide edit"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Label("Edit:", id="edit-label")
        yield Input(id="edit-input")

    def focus(self) -> None:
        self.query_one("#edit-input").focus()

    def on_blur(self) -> None:
        self.query_one("#edit-input").value = ""
