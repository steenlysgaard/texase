import pandas as pd
import pytest
from texase.data import get_mask
from texase.filter import Filter
from texase.table import TexaseTable
from textual.widgets._data_table import RowKey


@pytest.mark.asyncio
async def test_filter(loaded_app):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    filterbox = app.query_one("#filter-box")

    # Check status before adding filter
    assert not app.show_filter
    assert not filterbox.display
    assert app.data._filters == ()
    assert len(table.rows.keys()) == 2

    await pilot.press("/")

    assert app.show_filter
    assert filterbox.display

    # Write formu and complete the rest
    await pilot.press("f", "o", "r", "m", "u", "right")
    # Focus should still be on the filterkey text box
    filterkey_box = app.query_one("#filterkey")
    assert filterkey_box.has_focus

    await pilot.press("tab")
    # Focus should now be on the filteroperator Select
    filteroperator_select = app.query_one("#filteroperator")
    assert filteroperator_select.has_focus

    await pilot.press("tab")
    filtervalue_box = app.query_one("#filtervalue")
    assert filtervalue_box.has_focus

    # Filter Au
    await pilot.press("A", "u", "enter")

    # Check that the filter box is not visible
    assert not app.show_filter
    assert not filterbox.display
    assert app.data._filters == (("formula", "==", "Au"),)
    assert len(table.rows.keys()) == 1

    # Remove filter
    await pilot.press("/")
    assert filterbox.display
    hit = await pilot.click("#remove-filter", offset=(1, 1))
    assert hit

    # The last filter is removed so the filterbox should be hidden
    assert not app.show_filter
    assert not filterbox.display
    assert app.data._filters == ()
    assert len(table.rows.keys()) == 2


@pytest.mark.asyncio
async def test_mark_with_filter(loaded_app):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    await pilot.press("/")

    # Toggle only mark
    await pilot.press("ctrl+t")

    # Filter Au
    await pilot.press("f", "o", "r", "m", "u", "right", "tab", "tab", "A", "u", "enter")

    assert len(table.rows.keys()) == 2
    assert table.marked_rows == {RowKey("1")}


@pytest.mark.asyncio
async def test_add_more_filters(loaded_app):
    app, pilot = loaded_app
    await pilot.press("/")
    await pilot.click("#add-filter")
    assert len(app.query(Filter)) == 2
    await pilot.press("ctrl+n")
    assert len(app.query(Filter)) == 3


@pytest.mark.asyncio
async def test_add_remove_filter(loaded_app):
    app, pilot = loaded_app
    filterbox = app.query_one("#filter-box")

    await pilot.press("/")
    assert app.show_filter
    assert filterbox.display

    await pilot.press("ctrl+r")
    assert not app.show_filter
    assert not filterbox.display

    await pilot.press("/")
    assert app.show_filter
    assert filterbox.display
    assert len(filterbox.query("#filterkey")) == 1
    assert filterbox.query("#filterkey")[-1].has_focus


@pytest.mark.parametrize(
    "series, op, value, expected",
    [
        # Int64Dtype with None
        (
            pd.Series([1, None, 3], dtype=pd.Int64Dtype()),
            "==",
            "3",
            pd.Series([False, False, True]),
        ),
        (
            pd.Series([None, 2, None], dtype=pd.Int64Dtype()),
            "!=",
            "2",
            pd.Series([True, False, True]),
        ),
        # BooleanDtype with None
        (
            pd.Series([True, None, False], dtype=pd.BooleanDtype()),
            "==",
            "true",
            pd.Series([True, False, False]),
        ),
        (
            pd.Series([None, False, None], dtype=pd.BooleanDtype()),
            "!=",
            "false",
            pd.Series([True, False, True]),
        ),
        # StringDtype with None
        (
            pd.Series(["apple", None, "banana"], dtype=pd.StringDtype()),
            "==",
            "apple",
            pd.Series([True, False, False]),
        ),
        (
            pd.Series([None, "banana", None], dtype=pd.StringDtype()),
            "!=",
            "banana",
            pd.Series([True, False, True]),
        ),
        # Standard cases
        (
            pd.Series([1, 2, 3], dtype=pd.Int64Dtype()),
            "==",
            "2",
            pd.Series([False, True, False]),
        ),
        (
            pd.Series([True, False], dtype=pd.BooleanDtype()),
            "!=",
            "true",
            pd.Series([False, True]),
        ),
        (
            pd.Series(["apple", "banana"], dtype=pd.StringDtype()),
            "==",
            "apple",
            pd.Series([True, False]),
        ),
        (
            pd.Series([1.5, 2.5], dtype="float"),
            ">",
            "2.0",
            pd.Series([False, True]),
        ),
        (
            pd.Series([1, 2, 3], dtype="int"),
            "<=",
            "2",
            pd.Series([True, True, False]),
        ),
        (
            pd.Series([None, "data", None], dtype="object"),
            "==",
            "data",
            pd.Series([False, True, False]),
        ),
        # Integers with NA
        (
            pd.Series([1, None, 3], dtype=pd.Int64Dtype()),
            ">",
            "2",
            pd.Series([False, False, True]),
        ),
        (
            pd.Series([4, None, 2], dtype=pd.Int64Dtype()),
            ">=",
            "2",
            pd.Series([True, False, True]),
        ),
        (
            pd.Series([1, None, 3], dtype=pd.Int64Dtype()),
            "<",
            "2",
            pd.Series([True, False, False]),
        ),
        (
            pd.Series([4, None, 2], dtype=pd.Int64Dtype()),
            "<=",
            "3",
            pd.Series([False, False, True]),
        ),
        # Floats with NA
        (
            pd.Series([1.5, None, 3.5], dtype="float"),
            ">",
            "2.5",
            pd.Series([False, False, True]),
        ),
        (
            pd.Series([4.5, None, 2.5], dtype="float"),
            ">=",
            "3.5",
            pd.Series([True, False, False]),
        ),
        (
            pd.Series([1.5, None, 3.5], dtype="float"),
            "<",
            "2.5",
            pd.Series([True, False, False]),
        ),
        (
            pd.Series([4.5, None, 2.5], dtype="float"),
            "<=",
            "4.5",
            pd.Series([True, False, True]),
        ),
    ],
)
def test_get_mask(series, op, value, expected):
    result = get_mask(series, op, value)
    pd.testing.assert_series_equal(result, expected, check_dtype=False)
