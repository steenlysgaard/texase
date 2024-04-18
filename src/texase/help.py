from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, Markdown

HELP_MARKDOWN_TOP = """\
# Help

[See also (clicking links doesn't work)](https://github.com/steenlysgaard/texase)

## Key bindings

"""

HELP_MARKDOWN_LEFT = """\
### Navigation

- `Arrow keys`: Move cursor
- `Home/End`: Go to top/bottom

### Manipulation

- `Space`: Mark/unmark row
- `u`: Unmark row
- `U`: Unmark all rows
- `#`: Delete marked rows (prompts y/n)
- `x`: Export marked rows to file (prompts for filename)
- `i`: Import rows from file (prompts for filename)

### Editing

- `e`: Edit field (if editable)
- `d`: Delete currently selected key-value-pair
- `k`: Add key-value-pair (prompts for key and value)

### More information

- `v`: View marked rows (if no rows are marked then view current row)
- `Enter`: Open details

"""

HELP_MARKDOWN_RIGHT = """\
### Filtering and searching

- `/`: Filter rows (prompts for filter string)
- `Ctrl-s`: Search rows (prompts for search string)

### Table appearance

- `s`: Sort by current column
- `+`: Add column
- `-`: Remove current selected column

### Misc

- `g`: Update table (from database)
- `Ctrl-g`: Hide all boxes, show only table
- `?`: Toggle this help
- `q`: Quit

"""


class HelpScreen(ModalScreen):
    BINDINGS = [("?", "pop_screen", "Toggle this help"),
                Binding("q", "pop_screen", "Hide help", show=False),
                Binding("ctrl+g", "pop_screen", "Hide help", show=False),
                ]
    
    DEFAULT_CSS = """
        HelpScreen {
            align: center middle;
        }

        #help-screen-container {
            width: auto;
            max-width: 80%;
            height: auto;
            max-height: 90%;
            padding: 2 4;
            align: center middle;
            background: $panel;
        }

        Container > VerticalScroll > Horizontal > Markdown {
            width: 50%;
        }

        Container > VerticalScroll > Horizontal {
            height: auto;
        }
"""
    def compose(self) -> ComposeResult:
        with Container(id='help-screen-container'):
            with VerticalScroll():
                yield Markdown(HELP_MARKDOWN_TOP, id="help-markdown-top")
                with Horizontal():
                    yield Markdown(HELP_MARKDOWN_LEFT, id="help-markdown-left")
                    yield Markdown(HELP_MARKDOWN_RIGHT, id="help-markdown-right")
        yield Footer()
