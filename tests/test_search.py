import pytest

from textual.widgets._data_table import RowKey

from asetui.app import ASETUI
from asetui.table import AsetuiTable
from asetui.filter import Filter

from .shared_info import test_atoms, get_column_labels


@pytest.mark.asyncio
async def test_search(big_db_path):
    app = ASETUI(path=big_db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        searchbox = app.query_one("#search-box")
        
        # Check status before adding filter
        assert not app.show_search_box
        assert not searchbox.display
        
