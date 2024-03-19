import pytest

from ase.db import connect

from texase.app import TEXASE
from texase.table import TexaseTable


@pytest.mark.asyncio
async def test_delete(loaded_app_with_big_db, big_db_path):
    app, pilot = loaded_app_with_big_db
    table = app.query_one(TexaseTable)
    # Delete the current row
    await pilot.press("#", "y")

    # Check that the row is gone
    # The cursor should now be on id=2
    assert str(table.get_cell_at(table.cursor_coordinate)) == "2"
    assert app.data.df["id"].iloc[0] == 2
    with pytest.raises(KeyError):
        assert connect(big_db_path).get(id=1)
        
        
        
@pytest.mark.asyncio
async def test_delete_marked_rows(loaded_app_with_big_db, big_db_path):
    app, pilot = loaded_app_with_big_db

    # Mark a couple of rows
    await pilot.press("down", "space", "space", "space", "#", "y")
    assert app.data.df["id"].iloc[0] == 1
    assert app.data.df["id"].iloc[1] == 5
    for i in [2, 3, 4]:
        with pytest.raises(KeyError):
            assert connect(big_db_path).get(id=i)
