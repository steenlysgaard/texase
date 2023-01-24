from collections import defaultdict
from dataclasses import dataclass
from typing import List, Union

import pandas as pd
from ase.db import connect
from ase.db.core import float_to_time_string, now
from ase.db.table import all_columns
from rich.text import Text


@dataclass
class Data:
    df: pd.DataFrame
    db_path: str
    user_keys: List[str]

    def string_df(self) -> pd.DataFrame:
        return self.df[all_columns].applymap(format_value, na_action="ignore")


def format_value(val) -> Union[Text, str]:
    if isinstance(val, str):
        return val
    elif isinstance(val, float):
        if abs(val) > 1e6 or abs(val) < 1e-4:
            format_spec = "#.3g"
        else:
            format_spec = ".2f"
        return Text("{1:{0}}".format(format_spec, val), justify="right")
    elif isinstance(val, int):
        return Text(str(val), justify="right")
    else:
        return str(val)


def instantiate_data(db_path: str, sel: str = "") -> Data:
    db = connect(db_path)
    df, user_keys = db_to_df(db, sel)
    return Data(df=df, db_path=db_path, user_keys=user_keys)


def db_to_df(db, sel="") -> tuple[pd.DataFrame, List[str]]:
    """Convert a db into a pandas.DataFrame.

    The columns are built using defaultdicts, and put into a
    dataframe in the end.

    """
    cols = defaultdict(list)
    user_keys = set()
    keys = all_columns
    i = 0
    for row in db.select(selection=sel):
        # default keys are always present
        for k in keys:
            cols[k].append(get_value(row, k))
        user_keys |= set(row.key_value_pairs.keys())
        for k in user_keys:
            cols[k].extend([pd.NaT] * (i - len(cols[k])) + [get_value(row, k)])
        i += 1
    df = pd.DataFrame(cols, index=cols["id"])
    df["id"] = df["id"].astype("int")
    return df, list(user_keys)


def get_value(row, key) -> str:
    """Get the value from the row to the dataframe."""
    if key == "age":
        value = float_to_time_string(now() - row.ctime)
    elif key == "pbc":
        value = "".join("FT"[int(p)] for p in row.pbc)
    else:
        value = row.get(key, pd.NaT)
    return value
