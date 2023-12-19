import pytest

from ase.db import connect
from ase import Atoms
from ase.data import chemical_symbols

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

# # Define another fixture that depends on the previous one
# @pytest.fixture
# def my_object_with_id(my_object):
#     my_object["id"] = 123
#     return my_object
