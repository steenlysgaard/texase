from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
from textual.containers import Container
from textual.reactive import var

from asetui.data import instantiate_data
from asetui.table import AsetuiTable
from asetui.details import Details
from asetui.search import SearchBar


class ASETUI(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "sort_column", "Sort"),
        ("f", "toggle_details", "Show details"),
        ("+", "add_column", "Add column"),
    ]
    CSS_PATH = "asetui.css"

    show_details = var(False)
    show_search = var(False)

    def __init__(self, path: str = "test/test.db") -> None:
        self.path = path
        super().__init__()

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield Footer()
        yield MiddleContainer(
            SearchBar(id="searchbar"), Details(id="details"), AsetuiTable(id="table")
        )

    def on_mount(self) -> None:
        # db data
        data = instantiate_data(self.path)

        # Table
        table = self.query_one(AsetuiTable)

        # Columns
        for col in data.df:
            if col in data.user_keys:
                continue
            table.add_column(col)

        # Populate rows by fetching data
        for row in data.string_df().itertuples(index=False):
            table.add_row(*row)

        table.focus()
        self.data = data

    def action_sort_column(self) -> None:
        # Get the highlighted column
        table = self.query_one(AsetuiTable)
        print(table.cursor_cell)

    def action_toggle_details(self) -> None:
        self.show_details = not self.show_details
        table = self.query_one(AsetuiTable)
        if self.show_details:
            # Get the highlighted row
            row, _ = table.cursor_cell
            self.query_one(Details).update_kvplist(*self.data.row_details(row))

            # Set focus on the details sidebar
            self.query_one(Details).set_focus()

        else:
            # Set focus back on the table
            table.focus()

    def watch_show_details(self, show_details: bool) -> None:
        """Called when show_details is modified."""
        dv = self.query_one(Details)
        dv.display = show_details

    def action_add_column(self) -> None:
        # Change this to True when the search bar is able to close
        # itself after a search.
        self.show_search = not self.show_search

    def watch_show_search(self, show_search: bool) -> None:
        searchbar = self.query_one(SearchBar)
        searchbar.display = show_search


class MiddleContainer(Container):
    pass


def main(path: str = "test.db"):

    app = ASETUI(path=path)
    app.run()


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
