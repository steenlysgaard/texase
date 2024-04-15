from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.suggester import Suggester
from textual.validation import Function
from textual.widgets import Button, Checkbox, Input, Select, Static
from textual.widgets._data_table import RowKey

from texase.data import ops
from texase.table import TexaseTable


class FilterBox(ScrollableContainer):
    BINDINGS = [
        # Hiding boxes shortcut is already defined in app, just
        # redefining the binding here to make it show in the filter
        # box
        ("ctrl+g", "hide_filter", "Hide filter(s)"),
        ("ctrl+t", "toggle_only_marked", "Toggle only marked"),
        ("ctrl+n", "add_filter", "New filter"),
        ("ctrl+r", "remove_filter", "Remove filter"),
    ]

    async def focus_filterbox(self) -> None:
        """Handle putting focus on the filterbox.

        If there are no filters, add a filter and put focus on the filterkey of that filter.
        If there are filters, go to the last filter then
            if the filter is disabled put focus on the + button
            else put focus on the filterkey.
        """

        filters = self.query("#filterkey")
        if len(filters) == 0:
            await self.add_filter()
            return

        # There could be more filters, so we focus on the last one
        if filters[-1].disabled:
            # The filter is disabled we focus on the + button instead
            self.query("#add-filter")[-1].focus()
        else:
            filters[-1].focus()

    def action_toggle_only_marked(self) -> None:
        """Toggle the only marked checkbox."""
        checkbox = self.query_one("#only-marked-checkbox")
        checkbox.value = not checkbox.value

    async def action_add_filter(self) -> None:
        await self.add_filter()

    async def add_filter(self) -> Filter:
        new_filter = Filter()
        await self.mount(new_filter)
        new_filter.scroll_visible()
        self.query("#filterkey")[-1].focus()
        return new_filter

    def action_remove_filter(self) -> None:
        """Remove the currently focused filter, alternatively the last
        filter.

        """
        filters = self.query(Filter)
        for filter in filters:
            if filter.has_focus_in_any_widget():
                filter.remove()
                break
        else:
            # If no filter has focus, remove the last filter
            if len(filters) > 0:
                filters[-1].remove()
        self.hide_if_no_filters()

    def compose(self) -> ComposeResult:
        yield Filter()
        yield Checkbox("Only mark filtered", id="only-marked-checkbox")

    async def on_button_pressed(self, pressed: Button.Pressed) -> None:
        """Called when a button is pressed."""
        if pressed.button.id == "remove-filter":
            # Remove the filter
            pressed.button.ancestors[0].remove()
            self.hide_if_no_filters()
        elif pressed.button.id == "add-filter":
            await self.add_filter()

    def hide_if_no_filters(self) -> None:
        """If there are no more filters hide the filter box."""
        if len(self.query(Filter)) == 0:
            self.app.show_filter = False


class Filter(Static):
    applied = False

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        """Called when the user presses enter on the filtervalue input."""
        input = submitted.input
        # Maybe not a great way to get the table
        app = self.ancestors[-1]
        if input.id == "filterkey":
            if input.value not in app.data.chosen_columns:
                self.notify(
                    f"Column {input.value} does not exist",
                    severity="warning",
                    title="Warning",
                )
            return

        key_input = self.query_one("#filterkey")
        op = self.query_one("#filteroperator")

        table = app.query_one(TexaseTable)
        filterbox = self.ancestors[0]
        if filterbox.query_one("#only-marked-checkbox").value:
            # Only mark
            filter_mask = app.data.get_mask_of_df_with_filter(
                (key_input.value, op.value, input.value)
            )
            for i in app.data.id_array_with_filter_and_sort(filter_mask):
                table.mark_row(RowKey(str(i)))
        else:
            # Filter
            table.add_filter(key_input.value, op.value, input.value)

            # Upon succesfully applying the filter, set the applied
            # variable to True
            self.applied = True

            # Disable the input widgets so they can't be changed, then it
            # is easier to remove them again
            input.disabled = True
            op.disabled = True
            key_input.disabled = True

        # Hide yourself
        app.show_filter = False

        # Focus on the table
        table.focus()

    def remove(self) -> None:
        # If this filter is applied to the data shown in the
        # table, it should be removed there as well

        if self.applied:
            key = self.query_one("#filterkey").value
            op = self.query_one("#filteroperator").value
            val = self.query_one("#filtervalue").value
            self.app.remove_filter_from_table((key, op, val))
        # After this the parent container takes care of removing this filter

        super().remove()

    def compose(self) -> ComposeResult:
        yield Button(
            Text("\uff0b", style="green"),
            id="add-filter",
            classes="filter-buttons",
            variant="primary",
        )
        yield Input(
            placeholder="Filter on column..",
            suggester=ColumnSuggester(self.ancestors[-1]),
            validate_on=["blur"],
            validators=[
                Function(
                    lambda x: x in self.app.data.chosen_columns, "Column does not exist"
                )
            ],
            id="filterkey",
        )
        yield Select(
            [(op, op) for op in ops.keys()],
            value="==",
            allow_blank=False,
            id="filteroperator",
        )
        yield Input(placeholder="Value", id="filtervalue")
        yield Button(
            Text("\u2212", style="red"),
            id="remove-filter",
            classes="filter-buttons",
            variant="warning",
        )

    def has_focus_in_any_widget(self) -> bool:
        """Return True if any widget in this container has focus."""
        for selector in [
            "#add-filter",
            "#filterkey",
            "#filteroperator",
            "#filtervalue",
            "#remove-filter",
        ]:
            if self.query_one(selector).has_focus:
                return True
        return False


class FilterSuggester(Suggester):
    """Give completion suggestions based either on columns or values
    of a single column."""

    def __init__(self, app, *, case_sensitive: bool = True) -> None:
        """Creates a suggester based off of a given iterable of possibilities.

        Args:
            suggestions: Valid suggestions sorted by decreasing priority.
            case_sensitive: Whether suggestions are computed in a case sensitive manner
                or not. The values provided in the argument `suggestions` represent the
                canonical representation of the completions and they will be suggested
                with that same casing.
        """
        super().__init__(case_sensitive=case_sensitive)
        self._app = app


class ColumnSuggester(FilterSuggester):
    async def get_suggestion(self, value: str) -> str | None:
        """Gets a completion from the given possibilities.

        Args:
            value: The current value.

        Returns:
            A valid completion suggestion or `None`.
        """
        possible_suggestions = self._app.data.chosen_columns
        for idx, suggestion in enumerate(possible_suggestions):
            if suggestion.startswith(value):
                return possible_suggestions[idx]
        return None
