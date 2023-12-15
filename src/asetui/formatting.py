from __future__ import annotations
from typing import Callable

import numpy as np
import pandas as pd
from rich.text import Text

from ase.db.core import float_to_time_string, now

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


def format_column(
    col: pd.Series, format_function: Callable = format_value
) -> pd.Series:
    return col.map(format_function, na_action="ignore").fillna("")


def get_age_string(ctime) -> str:
    return float_to_time_string(now() - ctime)


def convert_value_to_int_or_float(value):
    """Convert value to int or float if possible"""
    for t in [int, float]:
        try:
            value = t(value)
        except ValueError:
            pass
        else:
            break
    return value

def pbc_str_to_array(pbc_str: str) -> np.ndarray:
    """Convert e.g. the string TFT to [True, False, True]"""
    return np.array([c == "T" for c in pbc_str])
