import pytest
import numpy as np
import pandas as pd
from rich.text import Text

from asetui.data import Data, instantiate_data, format_column, apply_filter_and_sort_on_df
from asetui.formatting import format_value

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
    assert format_value(None) == ""


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
    expected_col = pd.Series(
        [
            Text("1", justify="right"),
            Text("2.34", justify="right"),
            "hello",
            "",
            Text("0.01", justify="right"),
            Text("1.00e+07", justify="right"),
        ]
    )
    # Assert that the formatted column is equal to the expected column
    assert formatted_col.equals(expected_col)


@pytest.fixture
def data(db_path):
    return instantiate_data(db_path)


def test_sort(data):
    # Expected output for sorting by id and age in descending order
    expected = np.array([2, 1])
    # Age is a special case so test for that specifically
    actual = data.sort(["age"], reverse=True)
    assert (actual == expected).all()
    # Actual output for sorting by id in descending order
    actual = data.sort(["id"], reverse=True)
    assert (actual == expected).all()
    # Sort on strings
    actual = data.sort(["formula"], reverse=False)
    assert (actual == expected).all()
    # Sort on something that's only present in one of the rows,
    # i.e. the row where the key is present should be first
    actual = data.sort(["float_key"], reverse=False)
    assert (actual == expected[::-1]).all()

    # How about mixed type columns?


@pytest.fixture
def filtered_data(data):
    data.add_filter("formula", "==", "Au")
    data.add_filter("id", "<", "5")
    return data


def test_filters_is_set(filtered_data):
    assert filtered_data._filters == (("formula", "==", "Au"), ("id", "<", "5"))


def test_add_filter(filtered_data):
    filtered_data.add_filter("id", ">", "1")
    assert filtered_data._filters == (
        ("formula", "==", "Au"),
        ("id", "<", "5"),
        ("id", ">", "1"),
    )


def test_remove_filter(filtered_data):
    filtered_data.remove_filter(("id", "<", "5"))
    assert filtered_data._filters == (("formula", "==", "Au"),)


def test_index_filtering(data):
    assert list(data.get_mask_of_df_with_filter(("id", "<", "2"))) == [True, False]


def test_df_caching(db_path):
    # Use a new Data instance so we get the correct hits, misses statistics
    data = instantiate_data(db_path)
    
    sdf = data.string_df()
    sdf.equals(data.string_df())
    assert data._string_df_cache.misses == 1
    assert data._string_df_cache.hits == 1
    
    data.column_for_print("id")
    assert data._string_column_cache.hits == 1
    
    # What if the df is modified? Then the cache should be invalidated.


def test_change_columns_caching(db_path):
    data = instantiate_data(db_path)
    sdf = data.string_df()
    data.chosen_columns.remove("magmom")
    assert not sdf.equals(data.string_df())

def test_apply_filter_and_sort_on_df():
    # create a sample DataFrame
    df = pd.DataFrame({'name': ['Alice', 'Bob', 'Charlie', 'David'], 'age': [25, 30, 35, 40]})
    # create a sample filter mask and sort array
    filter_mask = np.array([True, False, True, False])
    sort = np.array([2, 0, 3, 1])
    # create the expected output DataFrame
    expected = pd.DataFrame({'name': ['Charlie', 'Alice'], 'age': [35, 25]}, index=[2, 0])
    # apply the function and assert the result is equal to the expected output
    result = apply_filter_and_sort_on_df(df, filter_mask, sort)
    pd.testing.assert_frame_equal(result, expected)    
