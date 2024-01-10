import pytest
import pytest_asyncio

from ase.db import connect
from ase import Atoms
from ase.data import chemical_symbols

from asetui.app import ASETUI
from asetui.table import AsetuiTable, get_column_labels

from .shared_info import user_dct, cell, pbc, test_atoms

# Define a fixture that returns a dictionary object
@pytest.fixture
def db_path(tmp_path_factory):
    fn = tmp_path_factory.mktemp("test_db") / "test.db"
    db = connect(fn)
    db.write(Atoms(test_atoms[0], cell=cell, pbc=pbc),
             key_value_pairs=user_dct)
    db.write(Atoms(test_atoms[1]))
    return fn

# Define a fixture with a big db
@pytest.fixture
def big_db_path(tmp_path_factory):
    fn = tmp_path_factory.mktemp("test_db") / "test.db"
    db = connect(fn)
    for i in range(1, 100):
        db.write(Atoms(chemical_symbols[i], cell=cell, pbc=pbc),
                 key_value_pairs=user_dct)
    return fn

@pytest_asyncio.fixture
async def app_with_cursor_on_str_key(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(AsetuiTable)
        
        # Add an editable column, i.e. a user key
        await pilot.press("+", *list("str_key"), "enter")
        
        column_labels = get_column_labels(table.columns)
        idx = column_labels.index("str_key")
        # Move to the new column
        await pilot.press(*(idx * ("right", )))
        
        yield app, pilot

