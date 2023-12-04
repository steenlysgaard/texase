import pytest

from asetui.app import ASETUI
from asetui.keys import KeyBox, Key
from asetui.table import get_column_labels, AsetuiTable

@pytest.mark.asyncio
async def test_add_column_from_keybox(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(AsetuiTable)
        keybox = app.query_one(KeyBox)
        key_button = keybox.query_one("#key-str_key", Key)
        key_button.press()
        await pilot.pause()
        assert "str_key" in app.data.chosen_columns
        assert "str_key" in get_column_labels(table.columns)
        
        # Check that the key has been removed from the keybox
        assert len(keybox.query("#key-str_key")) == 0
