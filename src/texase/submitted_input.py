from collections.abc import Callable
from typing import Any

from textual.widgets import Input

from texase.formatting import convert_value_to_int_float_or_bool


def stop_and_notify_if_invalid_submission(
    submitted: Input.Submitted, notify_error: Callable[[str, str], None]
) -> bool:
    """Notify and stop event bubbling if widget validation failed."""
    if (
        submitted.validation_result is not None
        and not submitted.validation_result.is_valid
    ):
        notify_error(
            "\n".join(submitted.validation_result.failure_descriptions),
            "Invalid input",
        )
        submitted.stop()
        return True
    return False


def coerce_kvp_value(key: str, raw_value: str) -> Any:
    """Coerce KVP input value while preserving pbc semantics."""
    if key == "pbc":
        return raw_value.upper()
    return convert_value_to_int_float_or_bool(raw_value)
