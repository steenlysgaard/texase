import pytest

from ase.db import connect
from ase import Atoms

from .shared_info import user_dct, cell, pbc

# Define a fixture that returns a dictionary object
@pytest.fixture(scope="package")
def db_path(tmp_path_factory):
    fn = tmp_path_factory.mktemp("test_db") / "test.db"
    db = connect(fn)
    db.write(Atoms('Au', cell=cell, pbc=pbc),
             key_value_pairs=user_dct)
    db.write(Atoms('Ag'))
    return fn

# # Define another fixture that depends on the previous one
# @pytest.fixture
# def my_object_with_id(my_object):
#     my_object["id"] = 123
#     return my_object
