import pytest
from ase.db import connect
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


@pytest.mark.asyncio
async def test_delete_key_then_remove_from_keybox(loaded_app, db_path):
    app, pilot = loaded_app
    keybox = app.query_one(KeyBox)

    # Extra pause required since the KeyBox is added last
    await pilot.pause()

    # Remove the int_key kvp from id=1, so that all str_key values are
    # None, and check that the key is removed from the KeyBox
    connect(db_path).update(id=1, delete_keys=["int_key"])
    await pilot.press("g")
    await pilot.pause()

    assert "int_key" not in app.data.unused_columns()
    # Check that the key has been removed from the keybox
    assert len(keybox.query("#key-int_key")) == 0
