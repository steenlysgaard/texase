from typing import List

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label
from textual.containers import Container
from textual.reactive import var

from textual_autocomplete._autocomplete import AutoComplete, DropdownItem, Dropdown, InputState

from ase.visualize import view

from asetui.data import instantiate_data
from asetui.table import AsetuiTable
from asetui.details import Details
from asetui.search import SearchBar


class ASETUI(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "sort_column", "Sort"),
        ("f", "toggle_details", "Show details"),
        ("v", "view", "View"),
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
            SearchBar(Label("Search"),
                      AutoComplete(Searchbox(id="search-box", placeholder="Column to add.."),
                                   Dropdown(items=self.unused_columns)),
                      id="searchbar"),
            Details(id="details"),
            AsetuiTable(id="table"),
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
        
    def unused_columns(self, input_state: InputState) -> List[DropdownItem]:
        from ase.db.table import all_columns
        # Get the highlighted column
        table = self.query_one(AsetuiTable)
        used_columns = [tc.label.plain for tc in table.columns.values()]
        unused = []
        for col in self.data.user_keys + all_columns:
            if col not in used_columns:
                unused.append(DropdownItem(col))
        
        # Only keep columns that contain the Input value as a substring
        matches = [c for c in unused if input_state.value.lower() in c.main.plain.lower()]
        # Favour items that start with the Input value, pull them to the top
        ordered = sorted(matches, key=lambda v: v.main.plain.startswith(input_state.value.lower()))
        
        return ordered

    def action_sort_column(self) -> None:
        from ase.db.table import all_columns
        # Get the highlighted column
        table = self.query_one(AsetuiTable)
        used_columns = [tc.label.plain for tc in table.columns]
        unused = []
        for col in self.data.user_keys + all_columns:
            if col not in used_columns:
                unused.append(DropdownItem(col))
        print(unused)
        
        

    def action_toggle_details(self) -> None:
        self.show_details = not self.show_details
        table = self.query_one(AsetuiTable)
        if self.show_details:
            # Get the highlighted row
            row, _ = table.cursor_cell
            details = self.query_one(Details)
            details.update_kvplist(*self.data.row_details(row))
            details.update_data(self.data.row_data(row))

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
        self.query_one(Searchbox).focus()

    def watch_show_search(self, show_search: bool) -> None:
        searchbar = self.query_one(SearchBar)
        searchbar.display = show_search

    def action_view(self) -> None:
        table = self.query_one(AsetuiTable)
        atoms = self.data.get_atoms(table.cursor_cell[0])
        view(atoms)

    def on_list_view_selected(self):
        print("Selected on App")
        
    def on_input_submitted(self, submitted):
        print('here', submitted.value)


class MiddleContainer(Container):
    pass

class Searchbox(Input):
    pass


def main(path: str = "test.db"):

    app = ASETUI(path=path)
    app.run()


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
