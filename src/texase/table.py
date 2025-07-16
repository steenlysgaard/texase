from __future__ import annotations

import os
from typing import Iterable, List, Tuple, Union

from ase.gui.gui import GUI, Images
from rich.text import Text
from textual import on, work
from textual._two_way_dict import TwoWayDict
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.driver import Driver
from textual.widgets import DataTable, Input, Label
from textual.widgets._data_table import ColumnKey, RowKey, StringKey

from texase.data import ALL_COLUMNS, Data
from texase.edit import AddBox, EditBox
from texase.formatting import MARKED_LABEL, UNMARKED_LABEL, format_value
from texase.yesno import YesNoScreen

UNEDITABLE_COLUMNS = [c for c in ALL_COLUMNS if c not in ["pbc"]]


class TexaseTable(DataTable):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "show_help", "Help"),
        ("s", "sort_column", "Sort"),
        ("space", "mark_row", "Mark row"),
        Binding("enter", "toggle_details", "Show details", show=False),
        ("e", "edit", "Edit"),
        ("k", "add_key_value_pair", "Add key-value pair"),
        ("#", "delete_rows", "Delete row(s)"),
        ("d", "delete_key_value_pairs", "Delete key-value pair(s)"),
        ("x", "export_rows", "Export row(s)"),
        ("i", "import_rows", "Import structure(s)"),
        ("v", "view", "View"),
        Binding("+", "add_column_to_table", "Add column", show=False),
        Binding("-", "remove_column", "Hide column", show=False),
        Binding("u", "unmark_row", "Unmark row", show=False),
        Binding("U", "unmark_all", "Unmark all", show=False),
        Binding("ctrl+s", "search", "Search"),
        Binding("/", "filter", "Filter rows"),
        Binding("g", "update_view", "Update from database", show=False),
    ]

    marked_rows: set[int] = set()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gui: GUI | None = None

    def _manipulate_filters(
        self, filter_tuple: Tuple[str, str, str], add: bool = True
    ) -> None:
        # Clear the table, but not the columns
        self.clear()

        # Get the key, operator and value from the tuple
        key, operator, value = filter_tuple

        if add:
            # Add the filter to the data object
            self.ancestors[-1].data.add_filter(key, operator, value)
        else:
            # Remove the filter from the data object
            self.ancestors[-1].data.remove_filter(filter_tuple)

        # Rebuild the table
        self.populate_table(
            self.ancestors[-1].data, marked_rows=self.marked_rows, columns_cleared=False
        )

    def add_filter(self, key, operator, value) -> None:
        self._manipulate_filters((key, operator, value), add=True)

    def remove_filter(self, key, operator, value) -> None:
        self._manipulate_filters((key, operator, value), add=False)

    def populate_table(
        self,
        data: Data,
        marked_rows: Union[List[int], None] = None,
        *,
        columns_cleared: bool = True,
    ) -> None:
        # Columns
        if columns_cleared:
            for col in data.chosen_columns:
                self.add_column(col, key=col)

        # Get ready for handling marked rows
        marked_row_keys = set()

        # Populate rows by fetching data
        for row in data.df_for_print().itertuples(index=False):
            if marked_rows is not None and RowKey(str(row[0])) in marked_rows:
                row_key = self.add_row(*row, key=str(row[0]), label=MARKED_LABEL)
                marked_row_keys.add(row_key)
            else:
                row_key = self.add_row(*row, key=str(row[0]), label=UNMARKED_LABEL)
        self.marked_rows = marked_row_keys

    def action_import_rows(self) -> None:
        self.app.import_rows()

    def action_export_rows(self) -> None:
        ids = self.ids_to_act_on()
        self.app.export_rows(ids)

    def action_filter(self) -> None:
        self.app.show_filterbox()

    def action_search(self) -> None:
        self.app.show_search()

    def action_view(self) -> None:
        """View the currently selected images, if no images are
        selected then view the row the cursor is on"""
        if self.marked_rows:
            images = [self.app.data.get_atoms(id) for id in self.get_marked_row_ids()]
        else:
            images = [self.app.data.get_atoms(self.row_id_at_cursor())]
        self.gui = GUI(Images(images))
        # Only run if we are not doing a pytest
        if "PYTEST_CURRENT_TEST" not in os.environ:
            self.gui.run()

    def action_quit(self) -> None:
        self.app.quit_app()

    # Help screen
    def action_show_help(self) -> None:
        self.app.show_help()

    def action_add_column_to_table(self) -> None:
        """Add a column to the table."""
        # Show the add column box
        self.app.action_add_column()

    # Sorting
    def action_sort_column(self) -> None:
        # Get the highlighted column
        self.sort_table(self.column_at_cursor())

    def sort_table(self, col_name: str) -> None:
        # Save the row key of the current cursor position
        row_key = self.coordinate_to_cell_key(Coordinate(self.cursor_row, 0)).row_key

        # Sort the table
        ordered_index = self.app.data.sort(col_name)

        self._row_locations = TwoWayDict(
            {
                StringKey(str(key)): new_index
                for new_index, key in enumerate(ordered_index)
            }
        )
        self._update_count += 1
        self.refresh()

        # After finished sort make the cursor go to the same cell as before sorting
        self.cursor_coordinate = Coordinate(
            self._row_locations.get(row_key), self.cursor_column
        )

        # How sort does it:
        # self._row_locations = TwoWayDict(
        #     {key: new_index for new_index, (key, _) in enumerate(ordered_rows)}
        # )
        # self._update_count += 1
        # self.refresh()
        # table.sort(*self.sort_columns, reverse=self.sort_reverse)

    async def action_remove_column(self) -> None:
        """Remove the column that the cursor is on.

        Also remove the column from chosen_columns."""

        # Save the name of the column to remove
        cursor_column_index = self.cursor_column
        column_to_remove = str(self.ordered_columns[cursor_column_index].label)

        # Add the column to the KeyBox
        await self.app.add_key_to_keybox(column_to_remove)

        self.remove_column_from_table(column_to_remove)

    def remove_column_from_table(self, column_name: str) -> None:
        # Remove the column from the table in data
        self.app.data.remove_from_chosen_columns(column_name)

        # col_key = table.ordered_columns[cursor_column_index].key
        col_key = ColumnKey(column_name)
        self.remove_column(col_key)

    def add_table_rows(self, data: Data, indices: Iterable[int]) -> None:
        for row in data.df_for_print().iloc[indices].itertuples(index=False):
            self.add_row(*row, key=str(row[0]), label=UNMARKED_LABEL)

    def update_table_rows(self, data: Data, indices: Iterable[int]) -> None:
        for index in indices:
            row = data.df_for_print().iloc[index]
            # Iterate through the columns of row
            for col in data.chosen_columns:
                self.update_cell(RowKey(str(row.id)), ColumnKey(col), row[col])

    def check_columns(self, data: Data) -> None:
        """Check if the columns shown in the table are up-to-date with
        data.chosen_columns, if not remove from the table."""
        for col in list(self.columns.keys()):
            if col not in data.chosen_columns:
                self.remove_column(col)

    def add_column_and_values(self, column_name: str) -> None:
        """Add a column and its values to the table.

        It is assumed that the column is present in the data.

        Parameters
        ----------
        column_name : str
            The name of the column to add.
        """
        col_key = self.add_column(column_name, key=column_name)
        col_index = self.get_column_index(col_key)

        # Column_for_print gets the values in the same order
        # as shown in the table, thus we can just use
        # enumerate to get the row index
        values = self.app.data.column_for_print(column_name)
        for i, val in enumerate(values[:-1]):
            self.update_cell_at(Coordinate(i, col_index), val)

        # Clear _updated_cells to avoid a forced update for each cell
        # in the function _update_column_widths
        self._updated_cells.clear()

        self.update_cell_at(
            Coordinate(len(values) - 1, col_index),
            values.iloc[-1],
            update_width=True,
        )

    # Add/Delete key-value-pairs
    def action_add_key_value_pair(self) -> None:
        self.app.show_add_kvp = True
        addbox = self.app.query_one("#add-kvp-box", AddBox)
        self.update_add_box(addbox)
        addbox.focus()

    @work
    async def action_delete_key_value_pairs(self) -> None:
        if not self.is_cell_editable(uneditable_columns=ALL_COLUMNS):
            return
        question = self.delete_kvp_question()
        if await self.app.push_screen_wait(YesNoScreen(question)):
            self.delete_selected_key_value_pairs()

            # Remove in db and df
            column_name = self.column_at_cursor()
            self.app.data.update_value(
                self.ids_to_act_on(), column=column_name, value=None
            )

        # If no other key value pairs are present in the column, delete the column from the table
        self.app.data.clean_user_keys()
        self.check_columns(self.app.data)
        await self.app.populate_key_box()

    @on(Driver.SignalResume)
    @work
    async def action_update_view(self) -> None:
        """Check if the db has been updated since it was last read.

        If so update the table."""
        # if not self.data.is_df_up_to_date():
        remove_idx, update_idx, add_idx = self.app.data.updates_from_db()

        self.delete_rows([self.row_index_to_row_key(idx) for idx in remove_idx])

        self.add_table_rows(self.app.data, add_idx)
        self.update_table_rows(self.app.data, update_idx)

        self.check_columns(self.app.data)

        # Update the KeyBox
        await self.app.populate_key_box()

    # Edit
    def action_edit(self) -> None:
        if self.is_cell_editable():
            self.app.show_edit = True
            editbox = self.app.query_one("#edit-box", EditBox)
            self.update_edit_box(editbox)
            editbox.focus()

    def is_cell_editable(
        self, uneditable_columns: List[str] = UNEDITABLE_COLUMNS
    ) -> bool:
        # Check if current cell is editable
        coordinate = self.cursor_coordinate

        # Get current column name
        column_name = str(list(self.columns.values())[coordinate.column].label)
        if column_name in uneditable_columns:
            self.notify(
                f"Column {column_name} can not be edited!",
                severity="warning",
                title="Warning",
            )
            return False
        else:
            return True

    def update_row_editable_cells(self, key_value_pairs: dict) -> None:
        """Update the editable cells of a row.

        This should be called from details, thus it is assumed that
        the cursor position hasn't changed and we can just use the
        cursor row.

        Parameters
        ----------
        key_value_pairs : dict
            A dictionary of key-value pairs to update.

        """
        for key, value in key_value_pairs.items():
            # Check that the column is actually shown
            if key not in self.columns:
                continue

            # Get the column index
            col_index = self.get_column_index(key)

            # Update the cell
            self.update_cell_at(
                Coordinate(self.cursor_row, col_index),
                format_value(value),
                update_width=True,
            )

    def update_edit_box(self, editbox: EditBox) -> None:
        # Current cell should be editable
        coordinate = self.cursor_coordinate

        # Get current column name
        column_name = self.column_at_cursor()

        label_str = f"Edit [bold]{column_name} =[/bold]"
        editbox.query_one("#edit-label", Label).renderable = label_str

        # Get current cell value
        cell_value = self.get_cell_at(coordinate)
        editbox.query_one("#edit-input", Input).value = str(cell_value)

        # Special rules to edit e.g. pbc or volume (then get cell editor) etc.

    def update_cell_from_edit_box(self, new_value: Text | str) -> None:
        self.update_cell_at(self.cursor_coordinate, new_value, update_width=True)

    def column_at_cursor(self) -> str:
        """Return the name of the column at the cursor."""
        return str(list(self.columns.values())[self.cursor_column].label)

    # Add/Edit/Delete key value pairs
    def update_add_box(self, addbox: AddBox) -> None:
        # Set the value of the key input field to an empty string
        input_field = addbox.query_one("#add-input", Input)
        input_field.value = ""
        input_field.placeholder = "key = value"

        # Update label to show add kvp
        label_str = "Add/Edit key value pair:"
        addbox.query_one("#add-label", Label).renderable = label_str

    def update_cell_from_add_box(self, column: str, value: Text | str) -> None:
        # Is column already present in the table? If so update the cells
        if column in self.columns:
            column_key = ColumnKey(column)
            if len(self.marked_rows) > 0:
                marked_list = list(self.marked_rows)
                for row_key in marked_list[:-1]:
                    self.update_cell(row_key, column_key, value)
                self.update_cell(marked_list[-1], column_key, value, update_width=True)
            else:
                # Add the column to the current row
                self.update_cell_at(
                    Coordinate(self.cursor_row, self.get_column_index(column_key)),
                    value,
                    update_width=True,
                )
        # If not, add the column. The values is already set in the data.
        else:
            self.add_column_and_values(column)

    def delete_kvp_question(self) -> Text:
        """Return the question to ask when deleting a key value pair."""
        # Get the ids of the marked or currently selected rows
        ids = self.ids_to_act_on()
        no_rows = len(ids)

        # Get the column name
        column_name = self.column_at_cursor()

        # Create the question
        ids_str = re_range(ids)
        plural = [" ", "s "][no_rows > 1]
        q = f"Do you want to delete the key value pair{plural}"
        q += f"[bold]{column_name}[/bold] in row{plural}"
        q += f"with id{plural}" + f"[bold]{ids_str}[/bold]?"
        return Text.from_markup(q)

    def delete_selected_key_value_pairs(self) -> None:
        """Delete key value pairs of the currently highlighted
        column. If some rows are marked then delete the key value
        pairs of all marked rows, else delete the key value pair of
        the current row."""

        rows = self.row_keys_to_act_on()

        for row_key in rows:
            self.update_cell(
                row_key, self.column_index_to_column_key(self.cursor_column), ""
            )

    # Details sidebar
    def action_toggle_details(self) -> None:
        if self.app.toggle_show_details():
            # Get the highlighted row
            row_id = self.row_id_at_cursor()
            self.app.make_details_ready(row_id)
        else:
            # Set focus back on the table
            self.focus()

    # Delete rows
    @work
    async def action_delete_rows(self) -> None:
        """Delete the currently marked rows."""
        if await self.app.push_screen_wait(YesNoScreen(self.delete_row_question())):
            # Remove in db and df
            self.app.data.delete_rows_from_df_and_db(self.ids_to_act_on())

            # Then remove in table
            self.delete_selected_rows()

    def delete_row_question(self) -> Text:
        """Return the question to ask when deleting a key value pair."""
        # Get the ids of the marked or currently selected rows
        ids = self.ids_to_act_on()
        no_rows = len(ids)

        # Create the question
        ids_str = re_range(ids)
        plural = [" ", "s "][no_rows > 1]
        q = f"Do you want to delete the row{plural}"
        q += f"with id{plural}" + f"[bold]{ids_str}[/bold]?"
        return Text.from_markup(q)

    def delete_selected_rows(self) -> None:
        """Delete the currently selected rows from the table view."""
        self.delete_rows(self.row_keys_to_act_on())

    def delete_rows(self, row_keys: Iterable[RowKey]) -> None:
        for row_key in row_keys:
            self.remove_row(row_key)
            self.marked_rows.discard(row_key)

    # Selecting/marking rows
    def action_mark_row(self) -> None:
        row_key = self.row_index_to_row_key(self.cursor_row)
        self.toggle_mark_row(row_key)

        # Go to the next row after marking
        self.action_cursor_down()

        # # Best effort so far for highlighting the background of a row
        # marked_text = Text(style=table.get_component_styles("datatable--cursor").rich_style)
        # for column_index, cell in enumerate(table.get_row_at(row)):
        #     if isinstance(cell, Text):
        #         cell.style = table.get_component_styles("datatable--cursor").rich_style
        #         table.update_cell_at(Coordinate(row, column_index), cell)
        #     else:
        #         table.update_cell_at(Coordinate(row, column_index), marked_text + cell)

    def action_unmark_row(self) -> None:
        row_index = self.cursor_row
        row_key = list(self.rows.keys())[row_index]
        self.unmark_row(row_key)

        # Go to the next row after unmarking
        self.action_cursor_down()

    def action_unmark_all(self) -> None:
        # Remove all marked rows in one go, this requires a full table
        # refresh. I don't know if it would be faster to call
        # action_unmark_row() for each row.
        for row_key in self.marked_rows:
            self.rows[row_key].label = UNMARKED_LABEL
        self.marked_rows = set()
        self._update_count += 1
        self.refresh()

    def on_data_table_row_label_selected(
        self, selected: DataTable.RowLabelSelected
    ) -> None:
        self.toggle_mark_row(selected.row_key)
        self.update_row_after_mark_operation(row_index=selected.row_index)

    def toggle_mark_row(self, row_key: RowKey) -> None:
        if row_key in self.marked_rows:
            self.unmark_row(row_key)
        else:
            self.mark_row(row_key)

    def unmark_row(self, row_key: RowKey) -> None:
        """Unmark a row.

        If it's not marked, do nothing.
        """
        if row_key in self.marked_rows:
            self.marked_rows.remove(row_key)
            self.rows[row_key].label = UNMARKED_LABEL
            self.update_row_after_mark_operation(row_key=row_key)

    def mark_row(self, row_key: RowKey) -> None:
        """Mark a row.

        If it is already marked, then it stays marked.
        """
        self.rows[row_key].label = MARKED_LABEL
        self.marked_rows.add(row_key)

        self.update_row_after_mark_operation(row_key=row_key)

    def update_row_after_mark_operation(
        self, /, row_key: Union[RowKey, None] = None, row_index: Union[int, None] = None
    ) -> None:
        """Tell the table that something has changed so it will refresh properly"""
        self._update_count += 1
        if row_index is not None:
            self.refresh_row(row_index)
        elif row_key is not None:
            self.refresh_row(self.get_row_index(row_key))

    def get_marked_row_ids(self) -> List[int]:
        """Return the ids of the rows that are currently marked"""
        return [get_id_from_row(self.get_row(row_key)) for row_key in self.marked_rows]

    def row_id_at_cursor(self) -> int:
        """Return the row id at the cursor as an int."""
        return get_id_from_row(self.get_row_at(self.cursor_row))

    def ids_to_act_on(self) -> list[int]:
        """Get the ids of the rows to act on using the same logic as
        row_keys_to_act_on."""
        return sorted(
            [
                get_id_from_row(self.get_row(row_key))
                for row_key in self.row_keys_to_act_on()
            ]
        )

    def row_keys_to_act_on(self) -> list[RowKey]:
        """Get the row keys of the rows to act on. If some rows are marked,
        then return the row keys of those rows, otherwise return a list of the RowKey of
        the row where the cursor is."""
        return (
            list(self.marked_rows)
            if self.marked_rows
            else [self.row_index_to_row_key(self.cursor_row)]
        )

    def row_index_to_row_key(self, row_index) -> RowKey:
        """Return the row key of the row at the given row index"""
        return self.coordinate_to_cell_key(Coordinate(row_index, 0)).row_key

    def column_index_to_column_key(self, column_index) -> ColumnKey:
        """Return the column key of the column at the given column index"""
        return self.coordinate_to_cell_key(Coordinate(0, column_index)).column_key


def get_id_from_row(row) -> int:
    # This assumes that the first index of the row is the id
    return int(str(row[0]))


def get_column_labels(columns) -> list:
    return [str(c.label) for c in columns.values()]


def list_formatter(start: int, end: int, step: int) -> str:
    return f"{start}-{end}" if step == 1 else f"{start}-{end}:{step}"


def re_range(lst: list[int]) -> str:
    """Return a string representation of a list of integers.

    The integers are grouped into ranges if they are consecutive. The
    exact implementation is lifted from here:
    https://stackoverflow.com/questions/9847601/convert-list-of-numbers-to-string-ranges

    """
    n = len(lst)
    result = []
    scan = 0
    while n - scan > 2:
        step = lst[scan + 1] - lst[scan]
        if lst[scan + 2] - lst[scan + 1] != step:
            result.append(str(lst[scan]))
            scan += 1
            continue

        for j in range(scan + 2, n - 1):
            if lst[j + 1] - lst[j] != step:
                result.append(list_formatter(lst[scan], lst[j], step))
                scan = j + 1
                break
        else:
            result.append(list_formatter(lst[scan], lst[-1], step))
            return ",".join(result)

    if n - scan == 1:
        result.append(str(lst[scan]))
    elif n - scan == 2:
        result.append(",".join(map(str, lst[scan:])))

    return ",".join(result)
