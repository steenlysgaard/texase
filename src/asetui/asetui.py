from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header

from asetui.data import instantiate_data
from asetui.table import AsetuiTable


class ASETUI(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]
    # CSS_PATH = "slurm_table.css"

    def __init__(self, path: str = "test/test.db") -> None:
        self.path = path

        super().__init__()

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield Footer()
        yield AsetuiTable()

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


def main():
    import sys

    app = ASETUI(sys.argv[1])
    app.run()


if __name__ == "__main__":
    main()