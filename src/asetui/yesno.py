from rich.text import Text
from textual.screen import Screen
from textual.widgets import Footer, Label
from textual.binding import Binding
from textual.app import ComposeResult


class YesNoScreen(Screen[bool]):
    """Screen with a question that can be answered yes or no."""
    
    DEFAULT_CSS = """
    YesNoScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }

    YesNoScreen > Label {
        text-align: center;
        width: 50%;
        height: auto;
        border: heavy $warning;
        padding: 2 4;
    }
"""
    
    BINDINGS = [
        ("y", "yes", "Yes"),
        ("n", "no", "No"),
        Binding("Y", "yes", "Yes", show=False),
        Binding("N", "no", "No", show=False),
        Binding("ctrl+g", "no", "No", show=False),
    ]

    def __init__(self, question: Text) -> None:
        self.question = question
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label(self.question)
        yield Footer()

    def action_yes(self) -> None:
        self.dismiss(True)

    def action_no(self) -> None:
        self.dismiss(False)
    

    
    