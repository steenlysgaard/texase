import numpy as np
import pandas as pd
import pytest
from ase.db import connect
from texase.data import (
    Data,
    apply_filter_and_sort_on_df,
    db_to_df,
    instantiate_data,
    recommend_dtype,
)

from .shared_info import user_dct


def test_instantiating_data(data, db_path):
    assert isinstance(data, Data)
    assert data.db_path == db_path
    # Test that both lists contain the same keys
    assert set(data.user_keys) == set(list(user_dct))


@pytest.fixture
def data(db_path):
    return instantiate_data(db_path)


def test_sort(data):
    # Expected output for sorting by id and age in descending order
    expected = np.array([2, 1])
    # Age is a special case so test for that specifically
    data.sort("age")
    actual = data.sort("age")
    assert (actual == expected).all()
    # Actual output for sorting by id in descending order
    actual = data.sort("id")
    assert (actual == expected[::-1]).all()
    # Sort on strings
    actual = data.sort("formula")
    assert (actual == expected).all()
    # Sort on something that's only present in one of the rows,
    # i.e. the row where the key is present should be first
    actual = data.sort("float_key")
    assert (actual == expected[::-1]).all()

    # How about mixed type columns?


def test_db_to_df(db_path):
    df, user_keys = db_to_df(connect(db_path))
    assert isinstance(df, pd.DataFrame)
    assert isinstance(user_keys, list)

    assert set(user_keys) == set(list(user_dct))

    # Check that the user keys are in the df
    for key in user_keys:
        assert key in df.columns

    assert df["id"].equals(pd.Series([1, 2], name="id"))
    assert df["id"].dtype == "int"
    assert df["formula"].equals(pd.Series(["Au", "Ag"], name="formula", dtype="string"))
    assert df["float_key"].equals(
        pd.Series([4.2, None], name="float_key", dtype="float")
    )
    assert df["str_key"].equals(
        pd.Series(["hav", None], name="str_key", dtype="string")
    )
    assert df["int_key"].equals(
        pd.Series([42, None], name="int_key", dtype=pd.Int64Dtype())
    )
    assert df["age"].dtype == "float"
    assert df["pbc"].equals(pd.Series(["TTF", "FFF"], name="pbc", dtype="string"))
    assert df["calculator"].equals(
        pd.Series([None, None], name="calculator", dtype="string")
    )


# Test cases are structured as: input iterable, expected result
test_cases = [
    ([1, 2, 3], pd.Int64Dtype()),  # Only integers
    ([1.0, 2.0, 3.0], "float"),  # Only floats
    (["a", "b", "c"], pd.StringDtype()),  # Only strings
    (["a", "b", None], pd.StringDtype()),  # Strings with None
    ([True, False, True], pd.BooleanDtype()),  # Only booleans
    ([1, 2, None], pd.Int64Dtype()),  # Integers with None
    ([1, 2.5, 3], "object"),  # Mixed integers and floats
    ([1, "a", 3.5], "object"),  # Mixed types
    ([None, None, None], "object"),  # Only None values
    (["-2-3-34-42", None, 234], "object"),
    ([1, True, 45], "object"),
    ([1.0, True, 12], "object"),
    ([True, None, False], pd.BooleanDtype()),
]


@pytest.mark.parametrize("iterable, expected", test_cases)
def test_recommend_dtype(iterable, expected):
    assert recommend_dtype(iterable) == expected


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


def test_change_columns_caching(data):
    sdf = data.string_df()
    data.chosen_columns.remove("magmom")
    assert not sdf.equals(data.string_df())


def test_apply_filter_and_sort_on_df():
    # create a sample DataFrame
    df = pd.DataFrame(
        {"name": ["Alice", "Bob", "Charlie", "David"], "age": [25, 30, 35, 40]}
    )
    # create a sample filter mask and sort array
    filter_mask = np.array([True, False, True, False])
    sort = np.array([2, 0, 3, 1])
    # create the expected output DataFrame
    expected = pd.DataFrame(
        {"name": ["Charlie", "Alice"], "age": [35, 25]}, index=[2, 0]
    )
    # apply the function and assert the result is equal to the expected output
    result = apply_filter_and_sort_on_df(df, filter_mask, sort)
    pd.testing.assert_frame_equal(result, expected)


def test_updating_dtypes(data):
    # Check the initial dtype
    assert data.df["int_key"].dtype == pd.Int64Dtype()

    # We add a float to the int column, it should be converted to object
    data.update_value([2], "int_key", 2.3)
    assert data.df["int_key"].dtype == np.dtype("object")

    # Oops we realize that it was a mistake, we convert it back to int
    data.update_value([2], "int_key", 2)
    assert data.df["int_key"].dtype == pd.Int64Dtype()
