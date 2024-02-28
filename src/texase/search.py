from typing import Tuple
from textual.containers import Container
from textual.binding import Binding


class ColumnAdd(Container):
    pass


class Search(Container):
    _table = None
    _data = None
    _coordinates = []

    BINDINGS = [
        Binding("ctrl+s", "next", "Next match"),
        Binding("ctrl+r", "previous", "Previous match"),
    ]

    def set_current_cursor_coordinate(self) -> None:
        """Set the current cursor coordinate."""
        self._current_cursor_coordinate = self._table.cursor_coordinate

    def on_input_changed(self, input):
        if input.value != "":
            coordinates = self._data.search_for_string(input.value)

            self._coordinates = list(coordinates)

            if len(self._coordinates) > 0:
                self.move_cursor(self._coordinates[0])

    def move_cursor(self, coordinate: Tuple[int, int]) -> None:
        self._table.move_cursor(row=coordinate[0], column=coordinate[1])

    def on_input_submitted(self, input) -> None:
        """Hide the search box after pressing enter. But first clear
        the input field."""
        self.app.show_search_box = False
        self._table.focus()

    def action_next(self) -> None:
        """Move the cursor to the next match."""
        self.move_to_match()

    def action_previous(self) -> None:
        """Move the cursor to the previous match."""
        self.move_to_match(previous=True)

    def move_to_match(self, previous=False) -> None:
        """Move the cursor to the next or previous match."""
        direction = 1
        if previous:
            direction = -1

        if len(self._coordinates) == 0:
            return

        try:
            current_index = self._coordinates.index(self._table.cursor_coordinate)
        except ValueError:
            current_index = -1

        try:
            next_coordinate = self._coordinates[current_index + direction]
        except IndexError:
            next_coordinate = self._coordinates[0]

        self.move_cursor(next_coordinate)
