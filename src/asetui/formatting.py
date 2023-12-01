from __future__ import annotations

import pandas as pd
from rich.text import Text

# The labels showing marked and unmarked rows
MARKED_LABEL = Text("\u25cf", style="bright_yellow")
UNMARKED_LABEL = Text("\u2219", style="grey")

def format_value(val) -> Text | str:
    if isinstance(val, str):
        return val
    elif isinstance(val, float):
        if abs(val) > 1e6 or abs(val) < 1e-3:
            format_spec = "#.3g"
        else:
            format_spec = ".2f"
        return Text("{1:{0}}".format(format_spec, val), justify="right")
    elif isinstance(val, int):
        return Text(str(val), justify="right")
    else:
        return str(val)


def format_column(col: pd.Series, format_function=format_value) -> pd.Series:
    return col.map(format_function, na_action="ignore").fillna("")


