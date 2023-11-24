from typing import List, Union, Tuple, Set

from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.widgets import DataTable
from textual.widgets._data_table import RowKey

from ase.db.table import all_columns

from asetui.data import Data
from asetui.edit import EditBox
from asetui.formatting import MARKED_LABEL, UNMARKED_LABEL


class AsetuiTable(DataTable):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "toggle_help", "Help"),
        ("s", "sort_column", "Sort"),
        ("f", "toggle_details", "Show details"),
        ("e", "edit", "Edit"),
        ("v", "view", "View"),
        ("+", "add_column", "Add column"),
        ("-", "remove_column", "Remove column"),
        ("space", "mark_row", "Mark row"),
        Binding("u", "unmark_row", "Unmark row", show=False),
        Binding("U", "unmark_all", "Unmark all", show=False),
        Binding("ctrl+s", "search", "Search", show=False),
        Binding("/", "filter", "Filter rows"),
        Binding("<", "move_to_top", "Move the cursor to the top", show=False),
        Binding(">", "move_to_bottom", "Move the cursor to the bottom", show=False),
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("l", "cursor_right", "Cursor Right", show=False),
        Binding("h", "cursor_left", "Cursor Left", show=False),
    ]

    marked_rows: Set = set()

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
                self.add_column(col)

        # Get ready for handling marked rows
        marked_row_keys = set()

        # Populate rows by fetching data
        for row in data.string_df().itertuples(index=True):
            if marked_rows is not None and RowKey(row[0]) in marked_rows:
                row_key = self.add_row(*row[1:], key=row[0], label=MARKED_LABEL)
                marked_row_keys.add(row_key)
            else:
                row_key = self.add_row(*row[1:], key=row[0], label=UNMARKED_LABEL)
        self.marked_rows = marked_row_keys

    def is_cell_editable(self) -> bool:
        # Check if current cell is editable
        coordinate = self.cursor_coordinate

        # Get current column name
        column_name = str(list(self.columns.values())[coordinate.column].label)
        if column_name in all_columns:
            self.notify(
                f"Column {column_name} can not be edited!",
                severity="warning",
                title="Warning",
            )
            return False
        else:
            return True
        
    def update_edit_box(self, editbox: EditBox) -> None:
        # Check if current cell is editable
        coordinate = self.cursor_coordinate

        # Get current column name
        column_name = str(list(self.columns.values())[coordinate.column].label)

        label_str = f"Edit [bold]{column_name} =[/bold]"
        editbox.query_one("#edit-label").renderable = label_str

        # Get current cell value
        cell_value = self.get_cell_at(coordinate)
        editbox.query_one("#edit-input").value = str(cell_value)

        # Special rules to edit e.g. pbc or volume (then get cell editor) etc.
        
    def update_cell_from_edit_box(self, new_value: str) -> None:
        self.update_cell_at(self.cursor_coordinate, new_value, update_width=True)

    # Selecting/marking rows
    def action_mark_row(self) -> None:
        row_index = self.cursor_row
        row_key = self.coordinate_to_cell_key(Coordinate(row_index, 0)).row_key
        # row_key = list(self.rows.keys())[row_index]
        self.toggle_mark_row(row_key)

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

    def get_id_of_current_row(self) -> int:
        return get_id_from_row(self.get_row_at(self.cursor_row))


def get_id_from_row(row) -> int:
    # This assumes that the first index of the row is the id
    return int(str(row[0]))
