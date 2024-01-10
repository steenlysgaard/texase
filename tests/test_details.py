import pytest

import pandas as pd

from textual.coordinate import Coordinate
from textual.widgets import Input

from ase.db import connect

from asetui.app import ASETUI
from asetui.table import AsetuiTable, get_column_labels
from asetui.details import Details, KVPList, EditableItem
from asetui.formatting import pbc_str_to_array

from .shared_info import pbc

def get_key_index_and_item(details: Details, key: str = 'pbc') -> tuple[int, EditableItem]:
    kvp_list = details.query_one(KVPList)
    # pbc will always be present in the kvp list as it comes from the Atoms object
    for i, listitem in enumerate(kvp_list.children):
        item = listitem.get_child_by_type(EditableItem)
        if item.key == key:
            break
    return i, item  # type: ignore
        
@pytest.mark.asyncio
async def test_edit(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(AsetuiTable)
        details = app.query_one("#details", Details)
        
        # Check status
        assert not app.show_details
        assert not details.display
        
        await pilot.press("f")
        
        assert app.show_details
        assert details.display
        
        i, item = get_key_index_and_item(details)
        
        # Press down arrow to select the pbc row
        await pilot.press(*(i * ("down", )))

        # Modify pbc
        await pilot.press("enter")
        # Focus should go to the input widget
        input_widget = item.query_one(Input)
        assert input_widget.has_focus
        assert input_widget.value == "".join(['FT'[i] for i in pbc])

        # Delete the current value
        await pilot.press(*(3 * ("backspace", )))
        
        # Change the value
        inv_pbc = "".join(['FT'[int(not i)] for i in pbc])
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
async def test_cancel_edit(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        details = app.query_one("#details", Details)
        table = app.query_one(AsetuiTable)
        
        await pilot.press("f")
        
        i, _ = get_key_index_and_item(details)
        
        # Press down arrow to select the pbc row
        await pilot.press(*(i * ("down", )), "enter")
        
        # Modify pbc
        await pilot.press("enter", *(3 * ("backspace", )))

        # Change the value
        inv_pbc = "".join(['FT'[int(not i)] for i in pbc])
        await pilot.press(*list(inv_pbc), "enter")
        
        # Cancel the changes and hide the details
        await pilot.press("ctrl+g")
        
        assert details.modified_keys == set()

        # Check that the value was not changed
        column_labels = get_column_labels(table.columns)
        idx = column_labels.index("pbc")
        assert table.get_cell_at(Coordinate(table.cursor_row, idx)) == "".join(['FT'[i] for i in pbc])
        assert app.data.df.iloc[0]["pbc"] == "".join(['FT'[i] for i in pbc])
        assert all(connect(db_path).get(1).pbc == pbc)
        
        await pilot.press("f")
        _, item = get_key_index_and_item(details)
        input_widget = item.query_one(Input)
        assert input_widget.value == "".join(['FT'[i] for i in pbc])

@pytest.mark.asyncio
async def test_delete(app_with_cursor_on_str_key, db_path):
    app, pilot = app_with_cursor_on_str_key
    details = app.query_one("#details", Details)
    table = app.query_one(AsetuiTable)

    await pilot.press("f")

    i, _ = get_key_index_and_item(details, 'str_key')

    # Press down arrow to select the pbc row
    await pilot.press(*(i * ("down", )))

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
