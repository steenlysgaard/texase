import pytest

from asetui.app import ASETUI
from asetui.keys import KeyBox, Key

@pytest.mark.asyncio
async def test_add_column_from_keybox(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        keybox = app.query_one(KeyBox)
        key_button = keybox.query_one("#key-str_key", Key)
        key_button.press()
        # Why won't you wait for the button to be pressed???
        print(app.data.chosen_columns)
        assert "str_key" in app.data.chosen_columns
