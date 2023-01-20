import numpy as np
import pandas as pd

from ase import Atoms
from ase.db import connect
from asetui.data import db_to_df

user_dct = {"str_key": "hav", "float_key": 4.2, "int_key": 42}
cell = [2, 2, 2]
pbc = [1, 1, 0]

def create_db(path):
    db_file = path / 'test.db'
    db = connect(db_file)
    db.write(Atoms('Au', cell=cell, pbc=pbc),
             key_value_pairs=user_dct)
    db.write(Atoms('Ag'))
    
    return db

def test_df_creation(tmp_path):
    db = create_db(tmp_path)
    df, user_keys = db_to_df(db)
    assert sorted(user_dct.keys()) == sorted(user_keys)
    for k, v in user_dct.items():
        key_column = df[k]
        assert key_column.iloc[0] == v
        assert pd.isnull(key_column.iloc[1])
        
    assert np.isclose(df.volume.iloc[0], np.product(cell))
    assert df.pbc.iloc[0] == ''.join(['FT'[i] for i in pbc])
    assert df.formula.tolist() == ['Au', 'Ag']
    
    
