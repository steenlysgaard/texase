import pytest

from ase.db import connect

from texase.app import TEXASE
from texase.table import TexaseTable


@pytest.mark.asyncio
async def test_delete(big_db_path):
    app = TEXASE(path=big_db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(TexaseTable)
        # Delete the current row
        await pilot.press("#", "y")
        
        # Check that the row is gone
        # The cursor should now be on id=2
        assert str(table.get_cell_at(table.cursor_coordinate)) == "2"
        assert app.data.df["id"].iloc[0] == 2
        with pytest.raises(KeyError):
            assert connect(big_db_path).get(id=1)
        
        
        
