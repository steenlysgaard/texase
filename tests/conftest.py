import pytest
import pytest_asyncio

from ase.db import connect
from ase import Atoms
from ase.data import chemical_symbols

from texase.app import TEXASE
from texase.table import TexaseTable, get_column_labels

from .shared_info import user_dct, cell, pbc, test_atoms, user_data

# Define a fixture that returns a dictionary object
@pytest.fixture
def db_path(tmp_path_factory):
    fn = tmp_path_factory.mktemp("test_db") / "test.db"
    db = connect(fn)
    db.write(
        Atoms(test_atoms[0], cell=cell, pbc=pbc),
        key_value_pairs=user_dct,
        data=user_data,
    )
    db.write(Atoms(test_atoms[1]))
    return fn


# Define a fixture with a big db
@pytest.fixture
def big_db_path(tmp_path_factory):
    fn = tmp_path_factory.mktemp("test_db") / "test.db"
    db = connect(fn)
    for i in range(1, 100):
        db.write(
            Atoms(chemical_symbols[i], cell=cell, pbc=pbc), key_value_pairs=user_dct
        )
    return fn


@pytest_asyncio.fixture
async def loaded_app(db_path):
    app = TEXASE(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        await app.workers.wait_for_complete()

        yield app, pilot


@pytest_asyncio.fixture
async def app_with_cursor_on_str_key(loaded_app):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)

    # Add an editable column, i.e. a user key
    await pilot.press("+", *list("str_key"), "enter")

    column_labels = get_column_labels(table.columns)
    idx = column_labels.index("str_key")
    # Move to the new column
    await pilot.press(*(idx * ("right",)))

    yield app, pilot


@pytest_asyncio.fixture
async def loaded_app_with_big_db(big_db_path):
    app = TEXASE(path=big_db_path)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()

        yield app, pilot
