from __future__ import annotations

from typing import List, Union, Tuple, Set

from rich.text import Text
from textual import work
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.widgets import DataTable, Input, Label
from textual.widgets._data_table import RowKey, ColumnKey

from ase.db.table import all_columns

from texase.data import Data
from texase.edit import EditBox, AddBox
from texase.formatting import MARKED_LABEL, UNMARKED_LABEL, format_value

UNEDITABLE_COLUMNS = [c for c in all_columns if c not in ["pbc"]]

class TexaseTable(DataTable):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "toggle_help", "Help"),
        ("s", "sort_column", "Sort"),
        ("f", "toggle_details", "Show details"),
        ("e", "edit", "Edit"),
        ("K", "add_key_value_pair", "Add key-value pair"),
        # ("a", "add_configurations", "Add configuration(s)"),
        ("d", "delete_rows", "Delete row(s)"),
        ("D", "delete_key_value_pairs", "Delete key-value pair(s)"),
        ("v", "view", "View"),
        ("+", "add_column", "Add column"),
        ("-", "remove_column", "Hide column"),
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
        self.update_cell_at(
            Coordinate(len(values) - 1, col_index),
            values.iloc[-1],
            update_width=True,
        )
        
    def is_cell_editable(self, uneditable_columns: List[str] = UNEDITABLE_COLUMNS) -> bool:
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
        row_id : int
            The row id of the row to update.
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
            self.update_cell_at(Coordinate(self.cursor_row, col_index), format_value(value), update_width=True)

    def update_edit_box(self, editbox: EditBox) -> None:
        # Check if current cell is editable
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
        label_str = f"Add/Edit key value pair:"
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
        ids_str = ", ".join([str(id) for id in ids])
        plural = [" ", "s "][no_rows > 1]
        q = "Do you want to delete the key value pair" + plural
        q += f"[bold]{column_name}[/bold] in row" + plural
        q += "with id" + plural + f"[bold]{ids_str}[/bold]?"
        return Text.from_markup(q)
    
            
    def delete_selected_key_value_pairs(self) -> None:
        """Delete key value pairs of the currently hightlighted
        column. If some rows are marked then delete the key value
        pairs of all marked rows, else delete the key value pair of
        the current row."""
        
        rows = self.row_keys_to_act_on()
        
        for row_key in rows:
            self.update_cell(row_key, self.column_index_to_column_key(self.cursor_column), "")

    def delete_row_question(self) -> Text:
        """Return the question to ask when deleting a key value pair."""
        # Get the ids of the marked or currently selected rows
        ids = self.ids_to_act_on()
        no_rows = len(ids)
        
        # Create the question
        ids_str = ", ".join([str(id) for id in ids])
        plural = [" ", "s "][no_rows > 1]
        q = "Do you want to delete the row" + plural
        q += "with id" + plural + f"[bold]{ids_str}[/bold]?"
        return Text.from_markup(q)
    
    def delete_selected_rows(self) -> None:
        for row_key in self.row_keys_to_act_on():
            self.remove_row(row_key)
        self.marked_rows = set()
        
        
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

    def row_id_at_cursor(self) -> int:
        """Return the row id at the cursor as an int."""
        return get_id_from_row(self.get_row_at(self.cursor_row))

    def ids_to_act_on(self) -> List[int]:
        """Get the ids of the rows to act on using the same logic as
        row_keys_to_act_on."""
        return sorted([get_id_from_row(self.get_row(row_key))
                       for row_key in self.row_keys_to_act_on()])
    
    def row_keys_to_act_on(self) -> List[RowKey]:
        """Get the row keys of the rows to act on. If some rows are marked,
        then return the row keys of those rows, otherwise return a list of the RowKey of
        the row where the cursor is."""
        if self.marked_rows:
            rows = list(self.marked_rows)
        else:
            rows = [self.row_index_to_row_key(self.cursor_row)]
        return rows
    
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
