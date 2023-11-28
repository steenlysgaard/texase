import pytest

from textual.widgets._data_table import RowKey

from asetui.app import ASETUI
from asetui.table import AsetuiTable

@pytest.mark.asyncio
async def test_mark_row(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test() as pilot:
        table = app.query_one(AsetuiTable)
        assert not table.marked_rows
        
        # Mark the first row
        await pilot.press("space")
        assert table.marked_rows == {RowKey('1')}
        
        # Mark the second row
        await pilot.press("down", "space")
        assert table.marked_rows == {RowKey('1'), RowKey('2')}
        
        # Unmark the first row
        await pilot.press("up", "space")
        assert table.marked_rows == {RowKey('2')}
        
        # Unmark all rows
        await pilot.press("U")
        assert not table.marked_rows
        
        # Mark the first row
        await pilot.press("space")
        assert table.marked_rows == {RowKey('1')}
        
        # Unmark with u
        await pilot.press("u")
        assert not table.marked_rows
        
        # Mark with the mouse
        response = await pilot.click(selector=AsetuiTable, offset=(1, 2))
        assert response
        assert table.marked_rows == {RowKey('2')}
        
