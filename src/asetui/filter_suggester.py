from textual.suggester import Suggester

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
        self._suggestions = list(suggestions)
        self._for_comparison = (
            self._suggestions
            if self.case_sensitive
            else [suggestion.casefold() for suggestion in self._suggestions]
        )

class ColumnSuggester(FilterSuggester):
    async def get_suggestion(self, value: str) -> str | None:
        """Gets a completion from the given possibilities.

        Args:
            value: The current value.

        Returns:
            A valid completion suggestion or `None`.
        """
        for idx, suggestion in enumerate(self._for_comparison):
            if suggestion.startswith(value):
                return self._suggestions[idx]
        return None    
