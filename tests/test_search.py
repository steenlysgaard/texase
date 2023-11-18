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
