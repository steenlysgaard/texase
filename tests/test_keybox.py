import pytest
from texase.keys import Key, KeyBox
from texase.table import TexaseTable, get_column_labels


@pytest.mark.asyncio
async def test_add_column_from_keybox(loaded_app):
    app, pilot = loaded_app

    # Extra pause required since the KeyBox is added last
    await pilot.pause()

    table = app.query_one(TexaseTable)
    keybox = app.query_one(KeyBox)
    key_button = keybox.query_one("#key-str_key", Key)
    key_button.press()
    await pilot.pause()
    assert "str_key" in app.data.chosen_columns
    assert "str_key" in get_column_labels(table.columns)

    # Check that the key has been removed from the keybox
    assert len(keybox.query("#key-str_key")) == 0
