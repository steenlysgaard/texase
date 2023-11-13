import pytest

from asetui.app import ASETUI
from asetui.data import Data
from asetui.table import AsetuiTable

from .shared_info import user_dct, test_atoms

def get_column_labels(columns) -> list:
    return [str(c.label) for c in columns.values()]

@pytest.mark.asyncio
async def test_start_app(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test() as _:
        assert isinstance(app.data, Data)
        # Test that table is populated
        table = app.query_one(AsetuiTable)
        no_rows = len(table.rows.keys())
        assert no_rows == 2

        # Check that the table is populated with the correct data
        for i in range(no_rows):
            row_values = table.get_row_at(i)
            assert test_atoms[i] in row_values

        column_labels = [str(c.label) for c in table.columns.values()]
        assert 'formula' in column_labels

        assert list(table.get_column_at(column_labels.index('formula'))) == test_atoms
    
@pytest.mark.asyncio
async def test_add_column(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test() as pilot:
        table = app.query_one(AsetuiTable)
        # Check status before adding
        assert not app.show_column_add
        assert 'str_key' not in get_column_labels(table.columns)
        assert 'str_key' not in app.data.chosen_columns
        
        await pilot.press("+")
        # Check that the column add box is visible
        assert app.show_column_add
        assert app.query_one("#column-add-box").display
        
        # Type one of the user columns and tab complete
        await pilot.press("s", "t", "r", "tab", "enter")
        
        # Check that the column add box is not visible
        assert not app.show_column_add
        
        # Check that the column has been added
        assert 'str_key' in get_column_labels(table.columns)
        assert 'str_key' in app.data.chosen_columns
        
@pytest.mark.asyncio
async def test_remove_column(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test() as pilot:
        table = app.query_one(AsetuiTable)
        columns_init = get_column_labels(table.columns)
        assert 'magmom' in columns_init
        assert 'magmom' in app.data.chosen_columns
        
        magmom_index = columns_init.index('magmom')
        
        # Move to magmom column
        await pilot.press(*(magmom_index * ("right", )))
        assert table.cursor_column == magmom_index
        
        # Remove magmom column
        await pilot.press("-")
        assert 'magmom' not in get_column_labels(table.columns)
        assert 'magmom' not in app.data.chosen_columns

