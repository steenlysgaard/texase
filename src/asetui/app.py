from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header
from textual.widgets import Placeholder
from textual.containers import Container, Horizontal
from textual.reactive import var

from asetui.data import instantiate_data
from asetui.table import AsetuiTable
from asetui.details import DV

class ASETUI(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "sort_column", "Sort"),
        ("f", "toggle_details", "Show details")
    ]
    CSS_PATH = "asetui.css"
    
    show_details = var(False)

    def watch_show_details(self, show_details: bool) -> None:
        """Called when show_details is modified."""
        dv = self.query_one(DV)
        dv.display = show_details
        print('watched', f'{show_details}')
        # dv.styles.max_width = "25vh"
        # self.set_class(show_tree, "-show-tree")
        
    def __init__(self, path: str = "test/test.db") -> None:
        self.path = path
        super().__init__()

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield Footer()
        # yield Details(id="details")
        yield Horizontal(
            DV(id="details"),
            AsetuiTable(id="table")
        )

    def on_mount(self) -> None:
        # db data
        data = instantiate_data(self.path)

        # Table
        table = self.query_one(DataTable)

        # Columns
        for col in data.df:
            if col in data.user_keys:
                continue
            table.add_column(col)

        # Populate rows by fetching data
        for row in data.string_df().itertuples(index=False):
            table.add_row(*row)

        table.focus()
        
    def action_sort_column(self) -> None:
        # Get the highlighted column
        table = self.query_one(DataTable)
        print(table.cursor_cell)
        
    def action_toggle_details(self) -> None:
        self.show_details = not self.show_details
        table = self.query_one(DataTable)
        # details = self.query_one(DV)
        # details.make_visible(table.cursor_cell)


def main(path: str = 'test.db'):
    
    app = ASETUI(path=path)
    app.run()


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
