from contextlib import contextmanager

import numpy as np

from textual.coordinate import Coordinate

from ase import Atoms

from texase.table import TexaseTable
from texase.keys import KeyBox, Key

user_dct = {"str_key": "hav", "float_key": 4.2, "int_key": 42}
cell = [2, 2, 2]
pbc = [1, 1, 0]
user_data = {'string': 'hello',
             'number': 42,
             'float': 3.14,
             'boolean': True,
             'list': [1, 2, 3],
             'dict': {'a': 1, 'b': 2},
             'nparray': np.array([1, 2, 3]),
             'mixed_list': [1, 'a', 3.14],
             'nested_dict': {'a': {'b': 1}},
             }

test_atoms = ["Au", "Ag"]

def water_to_add() -> Atoms:
    atoms = Atoms('H2O')
    atoms.info['key_value_pairs'] = {'number1': 58}
    return atoms

def check_that_water_were_added_to_small_db(app):
    table = app.query_one(TexaseTable)
    
    assert len(table.rows) == 3

    # Check that new user keys are imported, but not shown yet
    assert 'number1' in app.data.unused_columns()

    # Check that the new user key is shown in the KeyBox
    keybox = app.query_one(KeyBox)
    keybox.query_one("#key-number1", Key)  # Will fail if not found

    # Check that the table is populated with the correct data
    assert app.data.df['formula'].tolist()[-1] == 'H2O'
    # Check the third row (2) and formula column (3)
    assert table.get_cell_at(Coordinate(2, 3)) == 'H2O'

        
@contextmanager
def assert_notifications_increased_by_one(app):
    notifications_t0 = len(app._notifications)
    yield
    assert len(app._notifications) == notifications_t0 + 1
