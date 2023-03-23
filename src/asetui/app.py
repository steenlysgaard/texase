from typing import List

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label
from textual.widgets._data_table import StringKey
from textual.containers import Container
from textual.coordinate import Coordinate
from textual.reactive import var
from textual._two_way_dict import TwoWayDict

from textual_autocomplete._autocomplete import (
    AutoComplete,
    DropdownItem,
    Dropdown,
    InputState,
)

from ase.visualize import view
from ase.db.table import all_columns

from asetui.data import instantiate_data, Data
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
        ("-", "remove_column", "Remove column"),
    ]
    CSS_PATH = "asetui.css"

    show_details = var(False)
    show_search = var(False)

    def __init__(self, path: str = "test/test.db") -> None:
        self.path = path
        self.sort_columns = ["id"]
        self.sort_reverse = False
        super().__init__()

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield Footer()
        yield MiddleContainer(
            SearchBar(
                Label("Search"),
                AutoComplete(
                    Searchbox(id="search-box", placeholder="Column to add.."),
                    Dropdown(items=self.unused_columns),
                ),
                id="searchbar",
            ),
            Details(id="details"),
            AsetuiTable(id="table"),
        )

    def on_mount(self) -> None:
        # db data
        data = instantiate_data(self.path)

        # Table
        table = self.query_one(AsetuiTable)

        # Populate table with data using an external function
        populate_table(table, data)

        table.focus()
        self.data = data

    def unused_columns(self, input_state: InputState) -> List[DropdownItem]:
        # Get the highlighted column
        used_columns = self.data.chosen_columns
        unused = []
        for col in self.data.user_keys + all_columns:
            if col not in used_columns:
                unused.append(DropdownItem(col))

        # Only keep columns that contain the Input value as a substring
        matches = [
            c for c in unused if input_state.value.lower() in c.main.plain.lower()
        ]
        # Favour items that start with the Input value, pull them to the top
        ordered = sorted(
            matches, key=lambda v: v.main.plain.startswith(input_state.value.lower())
        )

        return ordered

    def action_sort_column(self) -> None:
        # Get the highlighted column
        table = self.query_one(AsetuiTable)
        col_name = str(
            table.columns[list(table.columns.keys())[table.cursor_column]].label
        )
        # col_key = table.columns[list(table.columns.keys())[table.cursor_column]].label.text
        if len(self.sort_columns) > 0 and col_name == self.sort_columns[0]:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_columns.insert(0, col_name)
            self.sort_reverse = False
        ordered_index = self.data.sort(self.sort_columns, self.sort_reverse)

        table._row_locations = TwoWayDict(
            {StringKey(key): new_index for new_index, key in enumerate(ordered_index)}
        )
        table._update_count += 1
        table.refresh()

        # How sort does it:
        # self._row_locations = TwoWayDict(
        #     {key: new_index for new_index, (key, _) in enumerate(ordered_rows)}
        # )
        # self._update_count += 1
        # self.refresh()
        # table.sort(*self.sort_columns, reverse=self.sort_reverse)

    def action_toggle_details(self) -> None:
        self.show_details = not self.show_details
        table = self.query_one(AsetuiTable)
        if self.show_details:
            # Get the highlighted row
            row = table.cursor_row
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
        self.show_search = True
        self.query_one(Searchbox).focus()

    def action_remove_column(self) -> None:
        """This is currently done by removing the column from the data
        object, clearing the table completely and then rebuilding the
        table"""
        table = self.query_one(AsetuiTable)
        # Save the name of the column to remove
        cursor_row_index, cursor_column_index = table.cursor_row, table.cursor_column
        column_to_remove = str(table.ordered_columns[cursor_column_index].label)
        # Remove the column from the table in data
        self.data.remove_from_chosen_columns(column_to_remove)
        # Clear the table including columns
        table.clear(columns=True)
        # Rebuilt the table with the currently chosen columns
        populate_table(table, self.data)
        # Put the cursor back on the same column
        table.cursor_coordinate = table.validate_cursor_coordinate(
            Coordinate(cursor_row_index, cursor_column_index)
        )

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
        # Check if value is a possible column
        if self.data.add_to_chosen_columns(submitted.value):
            self.query_one(Searchbox).value = ""
            self.show_search = False
            table = self.query_one(AsetuiTable)
            col_key = table.add_column(submitted.value)
            # NOTE: data and table rows should be in the same order
            values = self.data.string_column(submitted.value)
            table_rows = list(table.rows)
            for row, val in zip(table_rows[:-1], values[:-1]):
                table.update_cell(row, col_key, val)
            table.update_cell(
                table_rows[-1], col_key, values.iloc[-1], update_width=True
            )
            table.focus()

    def action_quit(self) -> None:
        self.data.save_chosen_columns()
        super().exit()


def populate_table(table: AsetuiTable, data: Data) -> None:
    # Columns
    for col in data.chosen_columns:
        table.add_column(col)

    # Populate rows by fetching data
    for row in data.string_df().itertuples(index=True):
        table.add_row(*row[1:], key=row[0])


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
