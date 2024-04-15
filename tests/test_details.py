import numpy as np
import pandas as pd
import pytest
from ase.db import connect
from texase.details import DataItem, Details, EditableItem, KVPList
from texase.formatting import pbc_str_to_array
from texase.table import TexaseTable, get_column_labels
from textual.coordinate import Coordinate
from textual.widgets import Input
from textual.widgets._data_table import ColumnKey, RowKey

from .shared_info import assert_notifications_increased_by_one, pbc, user_data


def get_key_index_and_item(
    details: Details,
    key: str = "pbc",
    id: str = "#dynamic_kvp_list",
    itemtype: EditableItem | DataItem = EditableItem,
) -> tuple[int, EditableItem | DataItem]:
    kvp_list = details.query_one(id)
    # pbc will always be present in the kvp list as it comes from the Atoms object
    for i, listitem in enumerate(kvp_list.children):
        item = listitem.get_child_by_type(itemtype)
        if item.key == key:
            break
    return i, item  # type: ignore


def get_data_index_and_item(
        details: Details, key: str = "pbc", id: str = "#datalist", itemtype=DataItem,
) -> tuple[int, DataItem]:
    return get_key_index_and_item(details, key, id, itemtype)


@pytest.mark.asyncio
async def test_edit(loaded_app, db_path):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    details = app.query_one("#details", Details)

    # Check status
    assert not app.show_details
    assert not details.display

    await pilot.press("enter")

    assert app.show_details
    assert details.display

    i, item = get_key_index_and_item(details)

    # Press down arrow to select the pbc row
    await pilot.press(*(i * ("down",)))

    # Modify pbc
    await pilot.press("enter")
    # Focus should go to the input widget
    input_widget = item.query_one(Input)
    assert input_widget.has_focus
    assert input_widget.value == "".join(["FT"[i] for i in pbc])

    # Delete the current value
    await pilot.press(*(3 * ("backspace",)))

    # Change the value
    inv_pbc = "".join(["FT"[int(not i)] for i in pbc])
    await pilot.press(*list(inv_pbc), "enter")

    assert details.modified_keys == {"pbc"}

    # Save the changes and hide the details
    await pilot.press("ctrl+s", "ctrl+g")

    assert not app.show_details
    assert not details.display

    # Check that the value was changed
    column_labels = get_column_labels(table.columns)
    idx = column_labels.index("pbc")
    assert table.get_cell_at(Coordinate(table.cursor_row, idx)) == inv_pbc
    assert app.data.df.iloc[0]["pbc"] == inv_pbc
    assert all(connect(db_path).get(1).pbc == pbc_str_to_array(inv_pbc))

@pytest.mark.asyncio
async def test_edit_changing_type(loaded_app, db_path):
    app, pilot = loaded_app
    details = app.query_one("#details", Details)

    await pilot.press("enter")

    i, _ = get_key_index_and_item(details, key="str_key")

    # Press down arrow to select the pbc row
    await pilot.press(*(i * ("down",)))
    
    # Changing str_key value type to int should produce a notification
    with assert_notifications_increased_by_one(app):
        await pilot.press("enter", "ctrl+u", "0", "enter")
        await pilot.pause()
    
    # Save the changes
    await pilot.press("ctrl+s")

    # Check that the value is updated in the dataframe
    assert app.data.df["str_key"].iloc[0] == 0
    assert connect(db_path).get(id=1).get("str_key") == 0
    

@pytest.mark.asyncio
async def test_cancel_edit(loaded_app, db_path):
    app, pilot = loaded_app
    details = app.query_one("#details", Details)
    table = app.query_one(TexaseTable)

    await pilot.press("enter")

    i, _ = get_key_index_and_item(details)

    # Press down arrow to select the pbc row
    await pilot.press(*(i * ("down",)), "enter")

    # Modify pbc
    await pilot.press("enter", *(3 * ("backspace",)))

    # Change the value
    inv_pbc = "".join(["FT"[int(not i)] for i in pbc])
    await pilot.press(*list(inv_pbc), "enter")

    # Cancel the changes and hide the details
    await pilot.press("ctrl+g")

    assert details.modified_keys == set()

    # Check that the value was not changed
    column_labels = get_column_labels(table.columns)
    idx = column_labels.index("pbc")
    assert table.get_cell_at(Coordinate(table.cursor_row, idx)) == "".join(
        ["FT"[i] for i in pbc]
    )
    assert app.data.df.iloc[0]["pbc"] == "".join(["FT"[i] for i in pbc])
    assert all(connect(db_path).get(1).pbc == pbc)

    await pilot.press("f")
    _, item = get_key_index_and_item(details)
    input_widget = item.query_one(Input)
    assert input_widget.value == "".join(["FT"[i] for i in pbc])


@pytest.mark.asyncio
async def test_delete_kvp(app_with_cursor_on_str_key, db_path):
    app, pilot = app_with_cursor_on_str_key
    details = app.query_one("#details", Details)
    table = app.query_one(TexaseTable)

    await pilot.press("enter")

    i, _ = get_key_index_and_item(details, "str_key")

    # Press down arrow to select the str_key row
    await pilot.press(*(i * ("down",)))

    # Delete the key
    await pilot.press("ctrl+d")

    assert details.deleted_keys == {"str_key"}

    # Save the changes and hide the details
    await pilot.press("ctrl+s", "ctrl+g")

    # Check that the value was deleted
    column_labels = get_column_labels(table.columns)
    idx = column_labels.index("str_key")
    assert table.get_cell_at(Coordinate(table.cursor_row, idx)) == ""
    assert app.data.df.iloc[0]["str_key"] is pd.NaT
    with pytest.raises(AttributeError):
        connect(db_path).get(1).str_key

@pytest.mark.asyncio
async def test_delete_data(app_with_cursor_on_str_key, db_path):
    app, pilot = app_with_cursor_on_str_key
    details = app.query_one("#details", Details)

    await pilot.press("enter", "tab")

    i, _ = get_data_index_and_item(details, key="number")

    # Press down arrow to select the str_key row
    await pilot.press(*(i * ("down",)))

    # Delete the key
    await pilot.press("ctrl+d")

    # Check that the error message is displayed
    await pilot.pause()
    assert len(app._notifications) == 1
    
    # Check that the value is still present
    assert connect(db_path).get(1).data['number'] == user_data['number']
        

@pytest.mark.asyncio
@pytest.mark.parametrize("key, value", list(user_data.items()))
async def test_presence_of_data(loaded_app, key, value):
    app, pilot = loaded_app
    details = app.query_one("#details", Details)

    await pilot.press("enter", "tab")  # Tab to the data part of the details

    _, item = get_data_index_and_item(details, key=key)

    input_widget = item.query_one(Input)

    assert input_widget.value == str(value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "key, value",
    [
        ("string", "bye"),
        ("number", 2),
        ("float", 2.0),
        ("boolean", False),
        ("list", [10, 20, 30]),
        ("dict", {"a": 10, "b": 20}),
        ("mixed_list", [10, "hello", 2.0, False]),
        ("nested_dict", {"a": {"b": 10, "c": 20}, "d": 30}),
    ],
)
async def test_edit_data(loaded_app, db_path, key, value):
    app, pilot = loaded_app
    details = app.query_one("#details", Details)

    await pilot.press("enter", "tab")  # Tab to the data part of the details

    i, _ = get_data_index_and_item(details, key=key)
    # Press down arrow to select correct row
    await pilot.press(
        *(i * ("down",)), "enter", "ctrl+u", *list(str(value)), "enter", "ctrl+s"
    )

    data = connect(db_path).get(1).data
    assert data[key] == value
    assert isinstance(data[key], type(value))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "key, input, value",
    [
        ("nparray", "np.array([10, 20, 30])", np.array([10, 20, 30])),
        ("nparray", "[10 20 30]", np.array([10, 20, 30])),
    ],
)
async def test_edit_array_data(loaded_app, db_path, key, input, value):
    app, pilot = loaded_app
    details = app.query_one("#details", Details)

    await pilot.press("enter", "tab")  # Tab to the data part of the details

    i, _ = get_data_index_and_item(details, key=key)
    # Press down arrow to select correct row
    await pilot.press(
        *(i * ("down",)), "enter", "ctrl+u", *list(input), "enter", "ctrl+s"
    )

    data = connect(db_path).get(1).data
    assert np.all(data[key] == value)
    assert isinstance(data[key], type(value))
