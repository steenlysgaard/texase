import pytest
import pandas as pd
from rich.text import Text

from asetui.data import format_value, Data, instantiate_data, db_to_df, format_column

from .shared_info import user_dct

def test_format_value_string():
    assert format_value("hello") == "hello"

def test_format_value_float():
    returned_text = format_value(1.23456)
    assert str(returned_text) == "1.23"
    assert returned_text.justify == "right"
    assert str(format_value(0.0000123456)) == "1.23e-05"

def test_format_value_int():
    assert str(format_value(123)) == "123"

def test_format_value_None():
    assert format_value(None) == "None"
    
def test_instantiating_data(data, db_path):
    assert isinstance(data, Data)
    assert data.db_path == db_path
    # Test that both lists contain the same keys
    assert set(data.user_keys) == set(list(user_dct))

def test_format_value_on_a_column():
    # Create a sample pandas series with different types of values
    col = pd.Series([1, 2.34, "hello", None, 1e-2, 1e7])
    # Apply the format_column function
    formatted_col = format_column(col)
    # Check the expected output
    expected_col = pd.Series([
        Text("1", justify="right"),
        Text("2.34", justify="right"),
        "hello",
        "",
        Text("0.01", justify="right"),
        Text("1.00e+07", justify="right")
    ])
    # Assert that the formatted column is equal to the expected column
    assert formatted_col.equals(expected_col)
    
@pytest.fixture
def data(db_path):
    return instantiate_data(db_path)

    
def test_sort(data):
    # Expected output for sorting by id and age in descending order
    expected = pd.Index([2, 1])
    # Age is a special case so test for that specifically
    actual = data.sort(["age"], reverse=True)
    assert actual.equals(expected)
    # Actual output for sorting by id in descending order
    actual = data.sort(["id"], reverse=True)
    assert actual.equals(expected)
    # Sort on strings
    actual = data.sort(["formula"], reverse=False)
    assert actual.equals(expected)
    # Sort on something that's only present in one of the rows,
    # i.e. the row where the key is present should be first
    actual = data.sort(["float_key"], reverse=False)
    assert actual.equals(expected[::-1])
    
    # How about mixed type columns?
    
