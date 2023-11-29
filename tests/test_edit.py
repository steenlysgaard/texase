import pytest

from ase.db import connect

from asetui.app import ASETUI
from asetui.table import AsetuiTable

from .shared_info import get_column_labels, user_dct

@pytest.mark.asyncio
async def test_edit(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(AsetuiTable)
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
        await pilot.press(*(idx * ("right", )))
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
        assert app.data._string_column_cache.get(("str_key", )).iloc[0] == user_dct["str_key"]
        
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
        assert app.data._string_column_cache.get(("str_key", )) is None

        
        
        

        
