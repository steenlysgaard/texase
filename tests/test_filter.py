import pytest

from textual.widgets._data_table import RowKey

from asetui.app import ASETUI
from asetui.table import AsetuiTable
from asetui.filter import Filter

from .shared_info import test_atoms, get_column_labels


@pytest.mark.asyncio
async def test_filter(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(AsetuiTable)
        filterbox = app.query_one("#filter-box")
        
        # Check status before adding filter
        assert not app.show_filter
        assert not filterbox.display
        assert app.data.filter == []
        assert len(table.rows.keys()) == 2
        
        await pilot.press("/")
        
        assert app.show_filter
        assert filterbox.display
        
        # Write formu and complete the rest
        await pilot.press("f", "o", "r", "m", "u", "right")
        # Focus should still be on the filterkey text box
        filterkey_box = app.query_one("#filterkey")
        assert filterkey_box.has_focus
        
        await pilot.press("tab")
        # Focus should now be on the filteroperator Select
        filteroperator_select = app.query_one("#filteroperator")
        assert filteroperator_select.has_focus
        
        await pilot.press("tab")
        filtervalue_box = app.query_one("#filtervalue")
        assert filtervalue_box.has_focus
        
        # Filter Au
        await pilot.press("A", "u", "enter")

        # Check that the filter box is not visible
        assert not app.show_filter
        assert not filterbox.display
        assert app.data.filter == [('formula', '==', 'Au')]
        assert len(table.rows.keys()) == 1
        
        # Remove filter
        await pilot.press("/")
        assert filterbox.display
        hit = await pilot.click("#remove-filter", offset=(1, 1))
        assert hit

        # The last filter is removed so the filterbox should be hidden
        assert not app.show_filter
        assert not filterbox.display
        assert app.data.filter == []
        assert len(table.rows.keys()) == 2
        
        
        
@pytest.mark.asyncio
async def test_mark_with_filter(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(AsetuiTable)
        await pilot.press("/")
        
        # Toggle only mark
        await pilot.press("ctrl+t")
        
        # Filter Au
        await pilot.press("f", "o", "r", "m", "u", "right", "tab", "tab", "A", "u", "enter")

        assert len(table.rows.keys()) == 2
        assert table.marked_rows == {RowKey(1)}

@pytest.mark.asyncio
async def test_add_more_filters(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        await pilot.press("/")
        await pilot.click("#add-filter")
        assert len(app.query(Filter)) == 2
        await pilot.press("ctrl+a")
        assert len(app.query(Filter)) == 3
