from textual.containers import Container
from textual.suggester import Suggester
from textual.widgets import Input

from asetui.table import AsetuiTable
class ColumnAdd(Container):
    pass

class Filter(Container):
    def on_input_submitted(self, input: Input) -> None:
        """Called when the user presses enter on the filtervalue input."""
        print(input.value)
        
        key = self.query_one("#filterkey").value
        op = self.query_one("#filteroperator").value
        
        # Not great way to get the table
        app = self.ancestors[-1]
        table = app.query_one(AsetuiTable)
        table.add_filter(key, op, input.value)
        
        # Hide yourself
        app.show_filter = False
        
        # Maybe clear the input
        
        # Focus on the table
        table.focus()
        

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
    
