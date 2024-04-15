from __future__ import annotations

import ast
import re
from typing import Callable

import numpy as np
import pandas as pd
from ase.db.core import check, float_to_time_string, now
from rich.text import Text

# The labels showing marked and unmarked rows
MARKED_LABEL = Text("\u25cf", style="bright_yellow")
UNMARKED_LABEL = Text("\u2219", style="grey")


def format_value(val) -> Text | str:
    if val is None:
        return ""
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


def convert_value_to_int_float_or_bool(value):
    """Convert value to int, float or bool if possible. Otherwise return the value as is.

    Modified from ASE.
    """
    try:
        return int(value)
    except ValueError:
        try:
            value = float(value)
        except ValueError:
            value = {"true": True, "false": False}.get(value.lower(), value)
        return value


def convert_str_to_other_type(str_value: str) -> Any:
    """Convert string to dict, list or np.ndarray if possible. Otherwise return the value as is."""
    try:
        return ast.literal_eval(str_value)
    except (SyntaxError, ValueError):
        # Maybe this is a numpy array
        if is_numpy_array(str_value):
            return np.array(string_to_list(str_value))
        return str_value

def string_to_list(input_string):
    # Remove np.array if present
    if 'np.array' in input_string:
        input_string = re.search(r'\[(.*)\]', input_string).group(0)
    
    # Replace spaces with commas for a proper list format if necessary
    if ' ' in input_string and ',' not in input_string:
        input_string = input_string.replace(' ', ', ')
    
    # Convert string to list
    return ast.literal_eval(input_string)
    

def is_numpy_array(s):
    """Match with a regexp one of these two patterns:

    '[1 2 3 ...]'
    and
    'np.array([1, 2, 3 ...])'

    Thanks to copilot for the pattern.
    """
    # Regular expression pattern to match arrays of exclusively numbers or strings
    number_array_pattern = r"\[\d+(\.\d+)?( \d+(\.\d+)?)*\]"
    string_array_pattern = r'\["[^"]*"( "[^"]*")*\]'
    numpy_number_array_pattern = r"np\.array\(\[\d+(\.\d+)?(, \d+(\.\d+)?)*\]\)"
    numpy_string_array_pattern = r'np\.array\(\["[^"]*"(, "[^"]*")*\]\)'

    # Combine the patterns to match either numbers or strings but not both
    combined_pattern = r"^({}|{}|{}|{})$".format(
        number_array_pattern,
        string_array_pattern,
        numpy_number_array_pattern,
        numpy_string_array_pattern,
    )

    # Search for the pattern in the string
    return bool(re.match(combined_pattern, s))


def pbc_str_to_array(pbc_str: str) -> np.ndarray:
    """Convert e.g. the string TFT to [True, False, True]"""
    return np.array([c == "T" for c in pbc_str.upper()])

def kvp_exception(key, value) -> str | None:
    """Check that key-value-pair is valid for ase.db

    It is ok to edit pbc, we make this check first."""

    if key == "pbc":
        try:
            check_pbc_string_validity(value)
        except ValueError as e:
            return str(e)
        return None

    try:
        check({key: value})
    except ValueError as e:
        # Notify that the key-value-pair is not valid with the
        # raised ValueError and then return
        return str(e)
    return None

def check_pbc_string_validity(string):
    # check if the string has exactly three characters
    if len(string) == 3:
        # convert the string to upper case
        string = string.upper()
        # loop through each character in the string
        for char in string:
            # check if the character is either t or f
            if char not in ["T", "F"]:
                # raise a ValueError with a descriptive message
                raise ValueError(f"{string} contains characters that are not T or F!")
        # return True if all characters are t or f
        return True
    else:
        # raise a ValueError with a descriptive message
        raise ValueError(f"{string} does not have exactly three characters!")

def correctly_typed_kvp(input_str: str) -> Tuple[str, Any]:
    """Convert the input string of the form 'key=value' to the correct
    type if possible. At this point the input should be validated,
    i.e. the value contains a = and the key/column is editable

    """
    # Split the input string into a key and a value
    key, value = input_str.split("=", 1)
    # Remove leading and trailing whitespace
    key = key.strip()
    value = value.strip()
    # Convert the value to the correct type if possible
    value = convert_value_to_int_float_or_bool(value)

    return key, value
