from textual.containers import Container
from textual.app import ComposeResult
from textual.widgets import Markdown

HELP_MARKDOWN = """\
# Help

[See also (clicking links doesn't work)](https://github.com/steenlysgaard/texase)

## Key bindings

- `h,j,k,l` or arrow keys: Movement
- `</>` or `home/end`: Go to top/bottom

<br>

- `Space`: Mark/unmark row
- `u`: Unmark row
- `U`: Unmark all rows
- `D`: Delete marked rows (prompts y/n)
- `x`: Export marked rows to file (prompts for filename)

<br>

- `v`: View marked rows (if no rows are marked then view current row)

<br>

- `/`: Filter rows (prompts for filter string)
- `Ctrl-s`: Search rows (prompts for search string)
- `e`: Edit field (if editable)

<br>

- `f`: Open details

<br>

- `+`: Add column
- `-`: Remove current selected column

<br>

- `Ctrl-g`: Hide all boxes, show only table
- `?`: Toggle this help
- `q`: Quit

"""


class Help(Container):
    def compose(self) -> ComposeResult:
        yield Markdown(HELP_MARKDOWN, id="help")
