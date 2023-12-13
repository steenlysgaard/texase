from typing import List

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input
from textual.widgets._data_table import StringKey, DataTable
from textual.binding import Binding
from textual.containers import Container
from textual.coordinate import Coordinate
from textual.reactive import var
from textual._two_way_dict import TwoWayDict

from ase.visualize import view
from ase.db.core import check

from asetui.data import instantiate_data
from asetui.table import AsetuiTable
from asetui.details import Details
from asetui.help import Help
from asetui.search import Search
from asetui.addcolumn import AddColumnBox
from asetui.filter import FilterBox
from asetui.edit import EditBox, AddBox
from asetui.formatting import format_value, convert_value_to_int_or_float
from asetui.keys import KeyBox


class ASETUI(App):
    BINDINGS = [
        Binding("ctrl+g", "hide_all", "Hide all boxes", show=False),
    ]

    CSS_PATH = "asetui.css"

    # variables that are watched. Remember also to add them to the
    # action_hide_all function
    show_details = var(False)
    show_help = var(False)
    show_add_column_box = var(False)
    show_search_box = var(False)
    show_filter = var(False)
    show_edit = var(False)
    show_add_kvp = var(False)

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
            FilterBox(id="filter-box", classes="topbox"),
            # Boxes docked at the bottom in the same layer of the table
            Search(
                Input(id="search-input", placeholder="Search.."),
                classes="bottombox",
                id="search-box",
            ),
            EditBox(id="edit-box", classes="bottombox"),
            AddBox(id="add-kvp-box", classes="bottombox"),
            AddColumnBox(id="add-column-box", classes="bottombox"),
            # Other boxes
            Details(id="details"),
            Help(id="help"),
            
            AsetuiTable(id="table"),
            KeyBox(id="key-box"),
        )

    def on_mount(self) -> None:
        # Table
        table = self.query_one(AsetuiTable)
        table.loading = True

        self.load_data(table)
        
    @work
    async def load_data(self, table: AsetuiTable) -> None:
        # db data
        data = instantiate_data(self.path)
        self.data = data

        # Populate table with data using an external function
        table.populate_table(data)
        await self.populate_key_box()  # type: ignore
        
        table.loading = False
        table.focus()
        

    async def populate_key_box(self) -> None:
        key_box = self.query_one(KeyBox)
        await key_box.populate_keys(self.data.unused_columns())
        
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
            details.clear_modified_keys()
            details.update_kvplist(*self.data.row_details(row_id))
            details.update_data(self.data.row_data(row_id))

            # Set focus on the details sidebar
            self.query_one(Details).set_focus()

        else:
            # Set focus back on the table
            table.focus()
            
    def save_details(self, key_value_pairs: dict, data: dict) -> None:
        
        table = self.query_one(AsetuiTable)
        table.update_row_editable_cells(key_value_pairs)
        
        row_id = table.row_id_at_cursor()
        for column, value in key_value_pairs.items():
            self.data.update_value(row_id, column, value)
        
    def watch_show_details(self, show_details: bool) -> None:
        """Called when show_details is modified."""
        dv = self.query_one(Details)
        dv.display = show_details

    def action_hide_all(self) -> None:
        self.show_details = False
        self.show_help = False
        self.show_add_column_box = False
        self.show_search_box = False
        self.show_filter = False
        self.show_edit = False
        self.show_add_kvp = False
        self.query_one(AsetuiTable).focus()

    # Help sidebar
    def action_toggle_help(self) -> None:
        self.show_help = not self.show_help

    def watch_show_help(self, show_help: bool) -> None:
        """Called when show_help is modified."""
        help_view = self.query_one(Help)
        help_view.display = show_help

    # Add key-value-pairs
    def action_add_key_value_pair(self) -> None:
        table = self.query_one(AsetuiTable)
        self.show_add_kvp = True
        addbox = self.query_one("#add-kvp-box", AddBox)
        table.update_add_box(addbox)
        addbox.focus()

    def watch_show_add_kvp(self, show_add_kvp: bool) -> None:
        box = self.query_one("#add-kvp-box")
        box.display = show_add_kvp

    # Edit
    def action_edit(self) -> None:
        table = self.query_one(AsetuiTable)
        if table.is_cell_editable():
            self.show_edit = True
            editbox = self.query_one("#edit-box", EditBox)
            table.update_edit_box(editbox)
            editbox.focus()

    def watch_show_edit(self, show_edit: bool) -> None:
        editbox = self.query_one("#edit-box")
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
        filterbox = self.query_one("#filter-box", FilterBox)
        await filterbox.focus_filterbox()

    def watch_show_filter(self, show_filter: bool) -> None:
        searchbar = self.query_one("#filter-box")
        searchbar.display = show_filter

    # Column action
    def action_add_column(self) -> None:
        self.show_add_column_box = True
        self.query_one("#add-column-box").focus()

    async def action_remove_column(self) -> None:
        """Remove the column that the cursor is on.

        Also remove the column from chosen_columns."""

        table = self.query_one(AsetuiTable)
        # Save the name of the column to remove
        cursor_column_index = table.cursor_column
        column_to_remove = str(table.ordered_columns[cursor_column_index].label)
        
        # Add the column to the KeyBox
        await self.query_one(KeyBox).add_key(column_to_remove)

        # Remove the column from the table in data
        self.data.remove_from_chosen_columns(column_to_remove)

        col_key = table.ordered_columns[cursor_column_index].key
        table.remove_column(col_key)

    def watch_show_add_column_box(self, show_box: bool) -> None:
        addcolumnbox = self.query_one(AddColumnBox)
        addcolumnbox.display = show_box

    def action_view(self) -> None:
        """View the currently selected images, if no images are
        selected then view the row the cursor is on"""
        table = self.query_one(AsetuiTable)
        if table.marked_rows:
            images = [self.data.get_atoms(id) for id in table.get_marked_row_ids()]
        else:
            images = [self.data.get_atoms(table.row_id_at_cursor())]
        view(images)

    def add_column_to_table_and_remove_from_keybox(self, column: str) -> None:
        """Add a column to the table and remove it from the KeyBox."""
        table = self.query_one(AsetuiTable)
        self.data.add_to_chosen_columns(column)
        table.add_column_and_values(column)
        self.query_one(KeyBox).remove_key(column)
        
    def on_input_submitted(self, submitted):
        table = self.query_one(AsetuiTable)
        if submitted.control.id == "add-column-input":
            if not submitted.validation_result.is_valid:
                return
            self.add_column_to_table_and_remove_from_keybox(submitted.value)

            self.show_add_column_box = False
            table.focus()
        elif submitted.control.id == "edit-input":
            # Update table
            table.update_cell_from_edit_box(submitted.value)

            # Update data
            self.data.update_value(
                ids=table.row_id_at_cursor(),
                column=table.column_at_cursor(),
                value=submitted.value,
            )

            # Go back to original view
            self.show_edit = False
            table.focus()

        elif submitted.control.id == "add-input":
            if not submitted.validation_result.is_valid:
                return
            # At this point the input should be validated, i.e. the
            # value contains a = and the key/column is editable
            # Split input value in key and value on =
            key, value = submitted.value.split("=")
            # Remove whitespace
            key = key.strip()
            value = convert_value_to_int_or_float(value.strip())

            if not self.is_kvp_valid(key, value):
                return

            # Update data
            if table.marked_rows:
                # If there are marked rows, add the key value pair to
                # all marked rows
                self.data.update_value(
                    ids=table.get_marked_row_ids(), column=key, value=value
                )
            else:
                # If there are no marked rows, add the key value pair
                # to the row the cursor is on
                self.data.update_value(
                    ids=table.row_id_at_cursor(), column=key, value=value
                )

            # Update table
            table.update_cell_from_add_box(key, format_value(value))

            # Go back to original view
            self.show_add_kvp = False
            table.focus()
            
    def is_kvp_valid(self, key, value):
        """Check that key-value-pair is valid for ase.db"""
        try:
            check({key: value})
        except ValueError as e:
            # Notify that the key-value-pair is not valid with the
            # raised ValueError and then return
            self.notify(
                str(e),
                severity="error",
                title="ValueError",
            )
            return False
        return True

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
