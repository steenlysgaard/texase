from textual.binding import Binding
from textual.widgets import DataTable


class AsetuiTable(DataTable):
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("l", "cursor_right", "Cursor Right", show=False),
        Binding("h", "cursor_left", "Cursor Left", show=False),
    ]
