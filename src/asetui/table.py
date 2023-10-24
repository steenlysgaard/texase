from typing import List, Union

from textual.binding import Binding
from textual.widgets import DataTable

from asetui.data import Data
from asetui.formatting import MARKED_LABEL, UNMARKED_LABEL

class AsetuiTable(DataTable):
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("l", "cursor_right", "Cursor Right", show=False),
        Binding("h", "cursor_left", "Cursor Left", show=False),
    ]

    marked_rows: List = []
    
    def add_filter(self, key, operator, value):
        # Clear the table, but not the columns
        self.clear()
        
        # Add the filter to the data object
        # Maybe rather have an add filter method so we can remove single filters as well
        self.ancestors[-1].data.filter((key, operator, value))
        
        # Rebuild the table
        self.populate_table(self.ancestors[-1].data,
                            marked_rows=self.marked_rows,
                            columns_cleared=False)

    def populate_table(self, data: Data,
                       marked_rows: Union[List[int], None] = None,
                       *,
                       columns_cleared: bool = True,
    ) -> None:
        # Columns
        if columns_cleared:
            for col in data.chosen_columns:
                self.add_column(col)

        # Get ready for handling marked rows
        marked_row_keys = []

        # Populate rows by fetching data
        for row in data.string_df().itertuples(index=True):
            if marked_rows is not None and row[0] in marked_rows:
                row_key = self.add_row(*row[1:], key=row[0], label=MARKED_LABEL)
                marked_row_keys.append(row_key)
            else:
                self.add_row(*row[1:], key=row[0], label=UNMARKED_LABEL)
        self.marked_rows = marked_row_keys

