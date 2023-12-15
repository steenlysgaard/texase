import numpy as np
import pandas as pd

from ase.db import connect
from asetui.data import db_to_df

from .shared_info import user_dct, cell, pbc

def test_df_creation(db_path):
    df, user_keys = db_to_df(connect(db_path))
    assert sorted(user_dct.keys()) == sorted(user_keys)
    for k, v in user_dct.items():
        key_column = df[k]
        assert key_column.iloc[0] == v
        assert pd.isnull(key_column.iloc[1])
        
    assert np.isclose(df.volume.iloc[0], np.prod(cell))
    assert df.pbc.iloc[0] == "".join(['FT'[i] for i in pbc])
    assert df.formula.tolist() == ['Au', 'Ag']
