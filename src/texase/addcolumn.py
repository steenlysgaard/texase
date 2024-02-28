from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.widgets import Input, Label
from textual.validation import Validator, ValidationResult

from texase.edit import EditBox
from texase.filter import FilterSuggester


class AddColumnBox(EditBox):
    input_widget_id = "add-column-input"
    label_id = "add-column-label"

    def compose(self) -> ComposeResult:
        yield Label("Add column:", id=self.label_id, classes="bottom-labels")
        yield Input(
            id=self.input_widget_id,
            classes="bottom-inputs",
            suggester=ColumnSuggester(self.app),
            validate_on=["submitted"],
            validators=[
                ValidColumn(app=self.app),
            ],
        )

    @on(Input.Submitted)
    def show_invalid_reasons(self, event: Input.Submitted) -> None:
        # Updating the UI to show the reasons why validation failed
        if not event.validation_result.is_valid:
            self.query_one(f"#{self.label_id}").add_class("-invalid")
            self.notify(
                "\n".join(event.validation_result.failure_descriptions),
                title="Invalid input",
                severity="error",
            )
        else:
            self.query_one(f"#{self.label_id}").remove_class("-invalid")


class ValidColumn(Validator):
    def __init__(self, *args, **kwargs) -> None:
        self._app = kwargs.pop("app", None)
        super().__init__(*args, **kwargs)

    def validate(self, value: str) -> ValidationResult:
        """Check if the value is an unused column."""
        if self._app.data.can_column_be_added(value):
            return self.success()
        else:
            return self.failure(f"{value} is not a valid column!")


class ColumnSuggester(FilterSuggester):
    async def get_suggestion(self, value: str) -> str | None:
        """Gets a completion from the unused columns in app.data.

        Args:
            value: The current value.

        Returns:
            A valid completion suggestion or `None`.
        """
        possible_suggestions = self._app.data.unused_columns()
        for idx, suggestion in enumerate(possible_suggestions):
            if suggestion.startswith(value):
                return possible_suggestions[idx]
        return None
