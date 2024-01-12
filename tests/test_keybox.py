import pytest

from texase.app import TEXASE
from texase.keys import KeyBox, Key
from texase.table import get_column_labels, TexaseTable

@pytest.mark.asyncio
async def test_add_column_from_keybox(db_path):
    app = TEXASE(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(TexaseTable)
        keybox = app.query_one(KeyBox)
        key_button = keybox.query_one("#key-str_key", Key)
        key_button.press()
        await pilot.pause()
        assert "str_key" in app.data.chosen_columns
        assert "str_key" in get_column_labels(table.columns)
        
        # Check that the key has been removed from the keybox
        assert len(keybox.query("#key-str_key")) == 0
