import pytest

import pandas as pd

from textual.widgets._data_table import ColumnKey, RowKey

from ase.db import connect

from texase.table import TexaseTable, get_column_labels
from texase.yesno import YesNoScreen

from .shared_info import user_dct


@pytest.mark.asyncio
async def test_edit(loaded_app, db_path):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    editbox = app.query_one("#edit-box")

    # Check status before adding filter
    assert not app.show_edit
    assert not editbox.display

    await pilot.press("e")

    # The cursor is on the id column, that shouldn't be editable
    assert not app.show_edit
    assert not editbox.display

    # Add an editable column, i.e. a user key
    await pilot.press("+", *list("str_key"), "enter")

    column_labels = get_column_labels(table.columns)
    idx = column_labels.index("str_key")
    # Move to the new column
    await pilot.press(*(idx * ("right",)))
    assert table.cursor_column == idx

    await pilot.press("e")
    assert app.show_edit
    assert editbox.display

    # Get the input value it should be as defined in user_dct
    assert editbox.query_one("#edit-input").value == user_dct["str_key"]

    # Change the value, but cancel and check that the value is unchanged
    await pilot.press("a", "b", "c", "ctrl+g", "e")
    assert editbox.query_one("#edit-input").value == user_dct["str_key"]
    # Also in the cache
    assert (
        app.data._string_column_cache.get(("str_key",)).iloc[0] == user_dct["str_key"]
    )

    # Change the value and accept
    await pilot.press("backspace", "a", "b", "c", "enter")
    new_str = user_dct["str_key"][:-1] + "abc"
    assert table.get_cell_at(table.cursor_coordinate) == new_str

    # Check that the value is updated in the edit box
    await pilot.press("e")
    assert editbox.query_one("#edit-input").value == new_str
    await pilot.press("ctrl+g")

    # Check that the value is updated in the dataframe
    assert app.data.df["str_key"].iloc[0] == new_str

    # And also updated in the db itself
    assert connect(db_path).get(id=1)["str_key"] == new_str

    # Also check that the respective column is discarded in the caches
    assert app.data._string_column_cache.get(("str_key",)) is None


@pytest.mark.asyncio
async def test_add_kvp(loaded_app, db_path):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    addbox = app.query_one("#add-kvp-box")

    # Check status before adding filter
    assert not app.show_add_kvp
    assert not addbox.display

    await pilot.press("k")

    assert app.show_add_kvp
    assert addbox.display

    # Check editing an existing kvp works
    new_str = "doh"
    await pilot.press(*list(f"str_key=  {new_str}"), "enter")
    assert app.data.df["str_key"].iloc[0] == new_str
    assert table.get_cell(RowKey("1"), ColumnKey("str_key")) == new_str
    # And also updated in the db itself
    assert connect(db_path).get(id=1)["str_key"] == new_str

    # Mark both rows and add a new kvp
    await pilot.press(
        "space", "down", "space", "k", *list(f"new_key={new_str}"), "enter"
    )
    for i in range(2):
        assert app.data.df["new_key"].iloc[i] == new_str
        assert table.get_cell(RowKey(str(i + 1)), ColumnKey("new_key")) == new_str
        assert connect(db_path).get(id=i + 1)["new_key"] == new_str

    # Check that converting values is handled correctly
    new_float = 6.6
    await pilot.press("k", *list(f"float_key  ={new_float}"), "enter")
    assert app.data.df["float_key"].iloc[1] == new_float
    assert str(table.get_cell(RowKey("2"), ColumnKey("float_key"))) == "6.60"
    assert connect(db_path).get(id=2)["float_key"] == new_float


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kvp",
    [
        "id=42",  # id is a reserved key
        # other invalid kvps
        "=43",
        "str_key=  ",
        "no equals sign",
        "A=3,B=5",
        "dict_key={'a': 3}",
    ],
)
async def test_invalid_kvps(loaded_app, kvp):
    app, pilot = loaded_app
    addbox = app.query_one("#add-kvp-box")

    await pilot.press("k", *list(kvp), "enter")
    # The add box is still present, i.e nothing has changed
    assert app.show_add_kvp
    assert addbox.display


@pytest.mark.asyncio
async def test_delete_single_kvp(app_with_cursor_on_str_key, db_path):
    app, pilot = app_with_cursor_on_str_key
    table = app.query_one(TexaseTable)

    # Press D and then n to cancel
    await pilot.press("d")
    assert isinstance(app.screen, YesNoScreen)
    await pilot.press("n")
    assert table.get_cell_at(table.cursor_coordinate) == user_dct["str_key"]

    # Press D and then y to delete
    await pilot.press("d", "y")
    assert table.get_cell_at(table.cursor_coordinate) == ""

    # Check that the value removed in the dataframe
    assert app.data.df["str_key"].iloc[0] is pd.NaT

    # And also removed in the db itself
    assert connect(db_path).get(id=1).get("str_key", None) is None


@pytest.mark.asyncio
async def test_delete_multiple_kvps(app_with_cursor_on_str_key, db_path):
    app, pilot = app_with_cursor_on_str_key

    table = app.query_one(TexaseTable)

    # Mark both rows and delete
    await pilot.press("space", "down", "space", "d", "y")
    for i in range(2):
        assert app.data.df["str_key"].iloc[i] is pd.NaT
        assert table.get_cell(RowKey(str(i + 1)), ColumnKey("str_key")) == ""
        assert connect(db_path).get(id=i + 1).get("str_key", None) is None


@pytest.mark.asyncio
async def test_edit_changing_type(app_with_cursor_on_str_key, db_path):
    app, pilot = app_with_cursor_on_str_key
    table = app.query_one(TexaseTable)

    await pilot.press("e", "ctrl+u", "0", "enter")
    # Changing str_key value type to int should produce a notification

    # Check that the message is displayed
    await pilot.pause()
    assert len(app._notifications) == 1

    # Check that the value is updated in the dataframe
    assert app.data.df["str_key"].iloc[0] == 0
    assert str(table.get_cell(RowKey(str(1)), ColumnKey("str_key"))) == "0"
    assert connect(db_path).get(id=1).get("str_key") == 0
