from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.suggester import Suggester
from textual.widgets import Input, Select, Button, Static, Checkbox
from textual.validation import Validator, ValidationResult, Function
from textual.widgets._data_table import RowKey
from rich.text import Text

from asetui.table import AsetuiTable
from asetui.data import ops

class FilterBox(ScrollableContainer):
    BINDINGS = [
        # Hiding boxes shortcut is already defined in app, just
        # redefining the binding here to make it show in the filter
        # box
        ("ctrl+g", "hide_filter", "Hide filter(s)"),
        ("ctrl+t", "toggle_only_marked", "Toggle only marked"),
    ]
    
    def action_toggle_only_marked(self) -> None:
        """Toggle the only marked checkbox."""
        checkbox = self.query_one("#only-marked-checkbox")
        checkbox.value = not checkbox.value
        
    def compose(self) -> ComposeResult:
        yield Filter()
        yield Checkbox("Only mark filtered", id="only-marked-checkbox")

class Filter(Static):
    applied = False
    
    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        """Called when the user presses enter on the filtervalue input."""
        input = submitted.input
        # Maybe not a great way to get the table
        app = self.ancestors[-1]
        if input.id == "filterkey":
            if input.value not in app.data.chosen_columns:
                self.notify(f"Column {input.value} does not exist",
                            severity="warning", title="Warning")
            return
        
        key_input = self.query_one("#filterkey")
        op = self.query_one("#filteroperator")
        
        table = app.query_one(AsetuiTable)
        filterbox = self.ancestors[0]
        if filterbox.query_one("#only-marked-checkbox").value:
            # Only mark
            indices = app.data.get_index_of_df_with_filter((key_input.value, op.value, input.value))
            for i in indices:
                table.mark_row(RowKey(i))
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
        
    def on_button_pressed(self, pressed: Button.Pressed) -> None:
        """Called when a button is pressed."""
        app = self.ancestors[-1]
        table = app.query_one(AsetuiTable)
        if pressed.button.id == "add-filter":
            app.add_filter()
        elif pressed.button.id == "remove-filter":
            # If this filter is applied to the data shown in the
            # table, it should be removed there as well
            if self.applied:
                key = self.query_one("#filterkey").value
                op = self.query_one("#filteroperator").value
                val = self.query_one("#filtervalue").value
                table.remove_filter(key, op, val)
                
            self.remove()
            
    def compose(self) -> ComposeResult:
        yield Button(Text("\uff0b", style="green"), id="add-filter", classes="filter-buttons")
        yield Input(placeholder="Filter on column..",
                    suggester=ColumnSuggester(self.ancestors[-1]),
                    validate_on=['blur'],
                    validators=[Function(lambda x: x in self.ancestors[-1].data.chosen_columns, "Column does not exist")],
                    id="filterkey")
        yield Select([(op, op) for op in ops.keys()],
                     value="==",
                     allow_blank=False,
                     id="filteroperator")
        yield Input(placeholder="Value",
                    id="filtervalue")
        yield Button(Text("\u2212", style="red"), id="remove-filter", classes="filter-buttons")
        

class FilterSuggester(Suggester):
    """Give completion suggestions based either on columns or values
    of a single column."""
    
    def __init__(
        self, app, *, case_sensitive: bool = True
    ) -> None:
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
        # self._suggestions = list(suggestions)
        # self._for_comparison = (
        #     self._suggestions
        #     if self.case_sensitive
        #     else [suggestion.casefold() for suggestion in self._suggestions]
        # )

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
    

# class ColumnValidator(Validator):
#     def validate(self, value: str) -> ValidationResult:


# class Palindrome(Validator):
#     def validate(self, value: str) -> ValidationResult:
#         def is_palindrome(value: str) -> bool:
#             return value == value[::-1]
#         return self.success() if is_palindrome(value) else self.failure("Not palindrome!")
    
