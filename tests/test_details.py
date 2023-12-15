import pytest

from textual.coordinate import Coordinate
from textual.widgets import Input

from ase.db import connect

from asetui.app import ASETUI
from asetui.table import AsetuiTable, get_column_labels
from asetui.details import Details, KVPList, EditableItem
from asetui.formatting import pbc_str_to_array

from .shared_info import pbc

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
        
        # Find pbc in the list
        kvp_list = details.query_one(KVPList)
        for i, listitem in enumerate(kvp_list.children):
            item = listitem.get_child_by_type(EditableItem)
            if item.key == "pbc":
                break
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
        
        # Also test cancelling
        
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

        
        
        

        
