from typing import List

from rich.text import Text

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label
from textual.widgets._data_table import StringKey, RowKey, DataTable
from textual.binding import Binding
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
from asetui.help import Help
from asetui.search import ColumnAdd, Search

# The labels showing marked and unmarked rows
MARKED_LABEL = Text("\u25cf", style="bright_yellow")
UNMARKED_LABEL = Text("\u2219", style="grey")


class ASETUI(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "toggle_help", "Help"),
        ("s", "sort_column", "Sort"),
        ("f", "toggle_details", "Show details"),
        ("v", "view", "View"),
        ("+", "add_column", "Add column"),
        ("-", "remove_column", "Remove column"),
        ("space", "mark_row", "Mark row"),
        Binding("u", "unmark_row", "Unmark row", show=False),
        Binding("U", "unmark_all", "Unmark all", show=False),
        Binding("ctrl+s", "search", "Search", show=False),
        Binding("ctrl+g", "hide_all", "Hide all boxes", show=False),
        Binding("<", "move_to_top", "Move the cursor to the top", show=False),
        Binding(">", "move_to_bottom", "Move the cursor to the bottom", show=False),
    ]
    CSS_PATH = "asetui.css"

    show_details = var(False)
    show_help = var(False)
    show_column_add = var(False)
    show_search_box = var(False)

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
            ColumnAdd(
                Label("Search"),
                AutoComplete(
                    Input(id="column-add-box", placeholder="Column to add.."),
                    Dropdown(items=self.unused_columns),
                ),
                classes="searchbar",
            ),
            Search(
                Label("Search"),
                Input(id="search-box", placeholder="Search.."),
                classes="searchbar",
            ),
            Details(id="details"),
            Help(id="help"),
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
        if not hasattr(self, "data"):
            # On first call data has not been set to the ASETUI object
            # so we have to cheat it
            return [DropdownItem("No match!")]

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

    # Sorting
    def action_sort_column(self) -> None:
        # Get the highlighted column
        table = self.query_one(AsetuiTable)
        col_name = str(
            table.columns[
                table.coordinate_to_cell_key(
                    Coordinate(0, table.cursor_column)
                ).column_key
            ].label
        )
        self.sort_table(col_name, table)

    def on_data_table_header_selected(self, selected: DataTable.HeaderSelected) -> None:
        table = selected.data_table
        col_name = str(selected.label)
        self.sort_table(col_name, table)

    def sort_table(self, col_name: str, table: AsetuiTable) -> None:
        # Save the row key of the current cursor position
        row_key = table.coordinate_to_cell_key(Coordinate(table.cursor_row, 0)).row_key

        # Sort the table
        if len(self.sort_columns) > 0 and col_name == self.sort_columns[0]:
            # If the column is already the first in the sort order, toggle the sort order
            self.sort_reverse = not self.sort_reverse
        else:
            # Otherwise, add the column to the sort order at first
            # position and set the sort order to ascending
            self.sort_columns.insert(0, col_name)
            self.sort_reverse = False
        ordered_index = self.data.sort(self.sort_columns, self.sort_reverse)

        table._row_locations = TwoWayDict(
            {StringKey(key): new_index for new_index, key in enumerate(ordered_index)}
        )
        table._update_count += 1
        table.refresh()

        # After finished sort make the cursor go to the same cell as before sorting
        table.cursor_coordinate = Coordinate(
            table._row_locations.get(row_key), table.cursor_column
        )

        # How sort does it:
        # self._row_locations = TwoWayDict(
        #     {key: new_index for new_index, (key, _) in enumerate(ordered_rows)}
        # )
        # self._update_count += 1
        # self.refresh()
        # table.sort(*self.sort_columns, reverse=self.sort_reverse)

    # Movement
    def action_move_to_top(self) -> None:
        table = self.query_one(AsetuiTable)
        table.cursor_coordinate = Coordinate(0, table.cursor_column)

    def action_move_to_bottom(self) -> None:
        table = self.query_one(AsetuiTable)
        table.cursor_coordinate = Coordinate(len(table.rows) - 1, table.cursor_column)

    # Selecting/marking rows
    def action_mark_row(self) -> None:
        table = self.query_one(AsetuiTable)
        row_index = table.cursor_row
        row_key = table.coordinate_to_cell_key(Coordinate(row_index, 0)).row_key
        # row_key = list(table.rows.keys())[row_index]
        toggle_mark_row(row_key, table)

        # Tell the table that something has changed so it will refresh properly
        table._update_count += 1
        table.refresh_row(row_index)

        # # Best effort so far for highlighting the background of a row
        # marked_text = Text(style=table.get_component_styles("datatable--cursor").rich_style)
        # for column_index, cell in enumerate(table.get_row_at(row)):
        #     if isinstance(cell, Text):
        #         cell.style = table.get_component_styles("datatable--cursor").rich_style
        #         table.update_cell_at(Coordinate(row, column_index), cell)
        #     else:
        #         table.update_cell_at(Coordinate(row, column_index), marked_text + cell)

    def action_unmark_row(self) -> None:
        table = self.query_one(AsetuiTable)
        row_index = table.cursor_row
        row_key = list(table.rows.keys())[row_index]
        if row_key in table.marked_rows:
            table.marked_rows.remove(row_key)
            table.rows[row_key].label = UNMARKED_LABEL
            table._update_count += 1
            table.refresh_row(row_index)

    def action_unmark_all(self) -> None:
        table = self.query_one(AsetuiTable)
        # Remove all marked rows in one go, this requires a full table
        # refresh. I don't know if it would be faster to call
        # action_unmark_row() for each row.
        for row_key in table.marked_rows:
            table.rows[row_key].label = UNMARKED_LABEL
        table.marked_rows = []
        table._update_count += 1
        table.refresh()

    def on_data_table_row_label_selected(
        self, selected: DataTable.RowLabelSelected
    ) -> None:
        table = selected.data_table
        toggle_mark_row(selected.row_key, table=table)
        table._update_count += 1
        table.refresh_row(selected.row_index)

    # Details sidebar
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

    def action_hide_all(self) -> None:
        self.show_details = False
        self.show_help = False
        self.show_column_add = False
        self.show_search_box = False
        self.query_one(AsetuiTable).focus()
        

    # Help sidebar
    def action_toggle_help(self) -> None:
        self.show_help = not self.show_help

    def watch_show_help(self, show_help: bool) -> None:
        """Called when show_help is modified."""
        help_view = self.query_one(Help)
        help_view.display = show_help

    # Search
    def action_search(self) -> None:
        # show_search_box is set to True since the search bar is able
        # to close itself after a search.
        self.show_search_box = True
        self.query_one("#search-box").focus()  # This is the input box
        
        search = self.query_one(Search)
        search._table = self.query_one(AsetuiTable)

    def watch_show_search_box(self, show_search_box: bool) -> None:
        searchbar = self.query_one(Search)
        searchbar.display = show_search_box

    # Column action
    def action_add_column(self) -> None:
        # Change this to True when the search bar is able to close
        # itself after a search.
        self.show_column_add = True
        self.query_one("#column-add-box").focus()

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
        # Remember marked rows before clearing the table
        marked_rows = self.get_marked_row_ids()
        # Clear the table including columns
        table.clear(columns=True)
        # Rebuilt the table with the currently chosen columns
        populate_table(table, self.data, marked_rows=marked_rows)
        # Put the cursor back on the same column
        table.cursor_coordinate = table.validate_cursor_coordinate(
            Coordinate(cursor_row_index, cursor_column_index)
        )

    def get_marked_row_ids(self) -> List[int]:
        """Return the ids of the rows that are currently marked"""
        table = self.query_one(AsetuiTable)
        return [
            get_id_from_row(table.get_row(row_key)) for row_key in table.marked_rows
        ]

    def watch_show_column_add(self, show_column_add: bool) -> None:
        searchbar = self.query_one(ColumnAdd)
        searchbar.display = show_column_add

    def action_view(self) -> None:
        """View the currently selected images, if no images are
        selected then view the row the cursor is on"""
        table = self.query_one(AsetuiTable)
        if table.marked_rows:
            images = [self.data.get_atoms(id) for id in self.get_marked_row_ids()]
        else:
            images = [
                self.data.get_atoms(get_id_from_row(table.get_row_at(table.cursor_row)))
            ]
        view(images)

    def on_list_view_selected(self):
        print("Selected on App")

    def on_input_submitted(self, submitted):
        if submitted.control.id == "column-add-box":
            # Check if value is a possible column
            if self.data.add_to_chosen_columns(submitted.value):
                self.query_one("#column-add-box").value = ""
                self.show_column_add = False
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


def get_id_from_row(row) -> int:
    # This assumes that the first index of the row is the id
    return int(str(row[0]))


def toggle_mark_row(row_key: RowKey, table: AsetuiTable) -> None:
    if row_key in table.marked_rows:
        table.marked_rows.remove(row_key)
        table.rows[row_key].label = UNMARKED_LABEL
    else:
        table.rows[row_key].label = MARKED_LABEL
        table.marked_rows.append(row_key)


def populate_table(
    table: AsetuiTable, data: Data, marked_rows: List[int] = None
) -> None:
    # Columns
    for col in data.chosen_columns:
        table.add_column(col)

    # Get ready for handling marked rows
    marked_row_keys = []

    # Populate rows by fetching data
    for row in data.string_df().itertuples(index=True):
        if marked_rows is not None and row[0] in marked_rows:
            row_key = table.add_row(*row[1:], key=row[0], label=MARKED_LABEL)
            marked_row_keys.append(row_key)
        else:
            table.add_row(*row[1:], key=row[0], label=UNMARKED_LABEL)
    table.marked_rows = marked_row_keys


class MiddleContainer(Container):
    pass


def main(path: str = "test.db"):

    app = ASETUI(path=path)
    app.run()


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
