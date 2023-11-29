from typing import List, Union

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label
from textual.widgets._data_table import StringKey, DataTable
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
from asetui.filter import FilterBox
from asetui.edit import EditBox


class ASETUI(App):
    BINDINGS = [
        Binding("ctrl+g", "hide_all", "Hide all boxes", show=False),
    ]

    CSS_PATH = "asetui.css"

    # variables that are watched. Remember also to add them to the
    # action_hide_all function
    show_details = var(False)
    show_help = var(False)
    show_column_add = var(False)
    show_search_box = var(False)
    show_filter = var(False)
    show_edit = var(False)

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
            # Boxes put centered at the top, but in a higher layer, of the table
            ColumnAdd(
                Label("Search"),
                AutoComplete(
                    Input(id="column-add-box", placeholder="Column to add.."),
                    Dropdown(items=self.unused_columns),
                ),
                classes="topbox",
            ),
            FilterBox(id="filter-box", classes="topbox"),
            # Boxes docked at the bottom in the same layer of the table
            Search(
                Input(id="search-input", placeholder="Search.."),
                classes="bottombox",
                id="search-box",
            ),
            EditBox(id="edit-box", classes="bottombox"),
            # Other boxes
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
        table.populate_table(data)

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

    def remove_filter_from_table(self, filter_tuple: tuple) -> None:
        self.query_one(AsetuiTable).remove_filter(*filter_tuple)

    # Sorting
    def action_sort_column(self) -> None:
        # Get the highlighted column
        table = self.query_one(AsetuiTable)
        self.sort_table(table.column_at_cursor(), table)

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
            # Otherwise, add/move the column to the sort order at first
            # position and set the sort order to ascending
            if col_name in self.sort_columns:
                self.sort_columns.remove(col_name)
            self.sort_columns.insert(0, col_name)
            self.sort_reverse = False
        ordered_index = self.data.sort(self.sort_columns, self.sort_reverse)

        table._row_locations = TwoWayDict(
            {
                StringKey(str(key)): new_index
                for new_index, key in enumerate(ordered_index)
            }
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

    # Details sidebar
    def action_toggle_details(self) -> None:
        self.show_details = not self.show_details
        table = self.query_one(AsetuiTable)
        if self.show_details:
            # Get the highlighted row
            row_id = table.row_id_at_cursor()
            details = self.query_one(Details)
            details.update_kvplist(*self.data.row_details(row_id))
            details.update_data(self.data.row_data(row_id))

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
        self.show_filter = False
        self.show_edit = False
        self.query_one(AsetuiTable).focus()

    # Help sidebar
    def action_toggle_help(self) -> None:
        self.show_help = not self.show_help

    def watch_show_help(self, show_help: bool) -> None:
        """Called when show_help is modified."""
        help_view = self.query_one(Help)
        help_view.display = show_help

    # Edit
    def action_edit(self) -> None:
        table = self.query_one(AsetuiTable)
        if table.is_cell_editable():
            self.show_edit = True
            editbox = self.query_one(EditBox)
            table.update_edit_box(editbox)
            editbox.focus()

    def watch_show_edit(self, show_edit: bool) -> None:
        editbox = self.query_one(EditBox)
        editbox.display = show_edit

    # Search
    def action_search(self) -> None:
        # show_search_box is set to True since the search bar is able
        # to close itself after a search.
        self.show_search_box = True
        search_input = self.query_one("#search-input")
        search_input.focus()  # This is the input box

        search = self.query_one(Search)
        search._table = self.query_one(AsetuiTable)
        search._data = self.data
        search_input.value = ""
        search.set_current_cursor_coordinate()

    def watch_show_search_box(self, show_search_box: bool) -> None:
        searchbar = self.query_one(Search)
        searchbar.display = show_search_box

    # Filter
    async def action_filter(self) -> None:
        self.show_filter = True
        filterbox = self.query_one("#filter-box")
        await filterbox.focus_filterbox()

    def watch_show_filter(self, show_filter: bool) -> None:
        searchbar = self.query_one("#filter-box")
        searchbar.display = show_filter

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
        marked_rows = table.get_marked_row_ids()
        # Clear the table including columns
        table.clear(columns=True)
        # Rebuilt the table with the currently chosen columns
        table.populate_table(self.data, marked_rows=marked_rows)
        # Put the cursor back on the same column
        table.cursor_coordinate = table.validate_cursor_coordinate(
            Coordinate(cursor_row_index, cursor_column_index)
        )

    def watch_show_column_add(self, show_column_add: bool) -> None:
        searchbar = self.query_one(ColumnAdd)
        searchbar.display = show_column_add

    def action_view(self) -> None:
        """View the currently selected images, if no images are
        selected then view the row the cursor is on"""
        table = self.query_one(AsetuiTable)
        if table.marked_rows:
            images = [self.data.get_atoms(id) for id in table.get_marked_row_ids()]
        else:
            images = [self.data.get_atoms(table.row_id_at_cursor())]
        view(images)

    def on_input_submitted(self, submitted):
        table = self.query_one(AsetuiTable)
        if submitted.control.id == "column-add-box":
            # Check if value is a possible column
            if self.data.add_to_chosen_columns(submitted.value):
                self.query_one("#column-add-box").value = ""
                self.show_column_add = False

                col_key = table.add_column(submitted.value)
                col_index = table.get_column_index(col_key)

                # Column_for_print gets the values in the same order
                # as shown in the table, thus we can just use
                # enumerate to get the row index
                values = self.data.column_for_print(submitted.value)
                for i, val in enumerate(values[:-1]):
                    table.update_cell_at(Coordinate(i, col_index), val)
                table.update_cell_at(
                    Coordinate(len(values) - 1, col_index),
                    values.iloc[-1],
                    update_width=True,
                )
                table.focus()
        elif submitted.control.id == "edit-input":
            # Update table
            table.update_cell_from_edit_box(submitted.value)

            # Update data
            self.data.update_value(
                idx=table.row_id_at_cursor(),
                column=table.column_at_cursor(),
                value=submitted.value,
            )

            # Go back to original view
            self.show_edit = False
            table.focus()

    def action_quit(self) -> None:
        self.data.save_chosen_columns()
        super().exit()


class MiddleContainer(Container):
    pass


def main(path: str = "test.db"):

    app = ASETUI(path=path)
    app.run()


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
