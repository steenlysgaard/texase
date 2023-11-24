import operator
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Union
from functools import wraps

import numpy as np
import pandas as pd
from ase.db import connect
from ase.db.core import float_to_time_string, now
from ase.db.table import all_columns
from ase import Atoms
from rich.text import Text
from textual.widgets import ListItem, Label
from textual._cache import LRUCache

from asetui.saved_columns import SavedColumns

ops = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
}

# If the operator is the key then convert the comparison value with
# the function specified in the value
def nothing(x):
    return x


def get_default_columns():
    return all_columns[:]


operator_type_conversion = {
    "<": float,
    "<=": float,
    "==": nothing,
    ">=": float,
    ">": float,
    "!=": nothing,
}


def cache(f):
    @wraps(f)
    def wrapper(self, *args, **kwds):
        cache_key = hash(tuple(args))
        cache = getattr(self, f.__name__ + "_cache")
        result = cache.get(cache_key, None)
        if result is not None:
            return result
        result = f(self, *args, **kwds)
        cache[cache_key] = result
        return result

    return wrapper


@dataclass
class Data:
    df: pd.DataFrame  # If df is changed, the cache needs to be cleared using e.g. self._df_cache.clear()
    db_path: Path
    user_keys: List[str]
    chosen_columns: list = field(default_factory=get_default_columns)
    saved_columns: Union[SavedColumns, None] = None
    data_filter: Union[List[Tuple[str, str, str]], None] = None

    def __post_init__(self):
        self._filters = tuple()
        if self.data_filter is not None:
            self.add_filter(*self.data_filter)
        self.db_path = Path(self.db_path).resolve()
        self.saved_columns = SavedColumns()
        self.update_chosen_columns()
        self._df_cache: LRUCache[Tuple, pd.DataFrame] = LRUCache(maxsize=128)
        self._string_df_cache: LRUCache[int, pd.DataFrame] = LRUCache(maxsize=128)
        self._string_column_cache: LRUCache[int, pd.Series] = LRUCache(maxsize=128)

    def string_column(self, column):
        return format_column(self.get_df()[column])

    def sort(self, columns, reverse):
        df = self.get_df()
        df.sort_values(columns, ascending=not reverse, inplace=True)
        return df.index

    def row_details(self, row) -> Tuple[Text, list]:
        """Returns key value pairs from the row in two items:"""
        static_kvps = ""
        dynamic_kvps = []
        editable_keys = self.user_keys + ["pbc"]
        for key, value in self.get_df().iloc[row].dropna().items():
            if key in editable_keys:
                dynamic_kvps.append(ListItem(Label(f"[bold]{key}: [/bold]{value}")))
            else:
                static_kvps += f"[bold]{key}: [/bold]{value}\n"
        return Text.from_markup(static_kvps[:-1]), dynamic_kvps

    def row_data(self, row: int) -> list:
        row_id = int(self.get_df().iloc[row].id)
        dynamic_data = []
        for key, value in get_data(self.db_path, row_id).items():
            dynamic_data.append(ListItem(Label(f"[bold]{key}: [/bold]{value}")))
        return dynamic_data

    def get_atoms(self, row) -> Atoms:
        db = connect(self.db_path)
        return db.get_atoms(id=row)

    def add_to_chosen_columns(self, column) -> bool:
        if column not in self.chosen_columns and column in all_columns + self.user_keys:
            self.chosen_columns.append(column)
            # chosen_columns now contain column, return True
            return True
        # Nothing has been added return False
        return False

    def remove_from_chosen_columns(self, column) -> bool:
        # Check that the column is in chosen_columns
        if column in self.chosen_columns:
            self.chosen_columns.remove(column)
            return True
        # Return False if nothing has changed
        return False

    def update_chosen_columns(self) -> None:
        # Check if db columns file exists. If so set chosen columns based on that.
        saved_columns = self.saved_columns[str(self.db_path)]
        if saved_columns is not None:
            self.chosen_columns = saved_columns

    def save_chosen_columns(self) -> None:
        self.saved_columns[str(self.db_path)] = self.chosen_columns

    def search_for_string(self, search_string: str):
        # Use the string representation of the dataframe, i.e. what is
        # currently visible
        df = self.string_df()  # Cache this somehow
        mask = np.column_stack(
            [
                df[col].astype(str).str.contains(search_string, na=False)
                for col in self.chosen_columns
            ]
        )
        return zip(*mask.nonzero())

    @property
    def filter(self) -> tuple:
        return self._filters

    def add_filter(self, key, operator, value) -> None:
        # We get the value as a string. Maybe we should convert it to
        # the correct type if the column values are not strings? But
        # how do we know? We try to deduce from the operator

        self._filters += ((key, operator, value),)

    def remove_filter(self, filter_tuple: Tuple[str, str, str]) -> None:
        self._filters = tuple(
            filter for filter in self._filters if filter != filter_tuple
        )

    @filter.setter
    def filter(self, _) -> None:
        raise NotImplementedError("Use add_filter instead")

    @filter.deleter
    def filter(self) -> None:
        self._filters = tuple()

    def string_df(self) -> pd.DataFrame:
        return self._string_df(self._filters, tuple(self.chosen_columns))

    @cache
    def _string_df(self, filters, chosen_columns) -> pd.DataFrame:
        """Get a representation of the DataFrame where all values are strings.

        This is used for displaying the data in the table. The
        function depends on self._filters and self.chosen_columns. The
        result is cached in self._string_df_cache. Thus the cache key
        needs to be built with self._filters and self.chosen_columns.

        """
        df_list = []
        for column in chosen_columns:
            df_list.append(self.get_string_column_from_df(column))
        return pd.concat(df_list, axis=1).fillna("", axis=1)

    def get_df(self, filters: tuple | None = None) -> pd.DataFrame:
        if filters is None:
            return self._df(self._filters)
        return self._df(filters)

    @cache
    def _df(self, filters: tuple = ()) -> pd.DataFrame:
        df = self.df
        for filter_key, op, filter_value in filters:
            df = df[ops[op](df[filter_key], operator_type_conversion[op](filter_value))]
        return df

    def get_index_of_df_with_filter(
        self, filter_tuple: Tuple[str, str, str]
    ) -> pd.Index:
        if not isinstance(filter_tuple[0], tuple):
            filter_tuple = (filter_tuple,)
        df = self.get_df(filter_tuple)
        return df.index

    def get_string_column_from_df(self, column: str) -> pd.Series:
        return self._string_column(self._filters, column)

    @cache
    def _string_column(self, filters, column) -> pd.Series:
        df = self.get_df()
        column_data = df[column]
        if column == "age":
            column_data = format_column(column_data, format_function=get_age_string)
        elif column == "pbc":
            column_data = format_column(column_data, format_function=get_pbc_string)
        return format_column(column_data)


def format_value(val) -> Union[Text, str]:
    if isinstance(val, str):
        return val
    elif isinstance(val, float):
        if abs(val) > 1e6 or abs(val) < 1e-3:
            format_spec = "#.3g"
        else:
            format_spec = ".2f"
        return Text("{1:{0}}".format(format_spec, val), justify="right")
    elif isinstance(val, int):
        return Text(str(val), justify="right")
    else:
        return str(val)


def format_column(col: pd.Series, format_function=format_value) -> pd.Series:
    return col.map(format_function, na_action="ignore").fillna("")


def instantiate_data(db_path: str, sel: str = "") -> Data:
    db = connect(db_path)
    df, user_keys = db_to_df(db, sel)
    return Data(df=df, db_path=Path(db_path), user_keys=user_keys)


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


def get_age_string(ctime) -> str:
    return float_to_time_string(now() - ctime)


def get_pbc_string(pbc) -> str:
    return "".join("FT"[int(p)] for p in pbc)


def get_value(row, key) -> str:
    """Get the value from the row to the dataframe."""
    if key == "age":
        # value = float_to_time_string(now() - row.ctime)
        value = row.ctime
    # elif key == "pbc":
    #     value = "".join("FT"[int(p)] for p in row.pbc)
    else:
        value = row.get(key, pd.NaT)
    return value


def get_data(db_path, row_id):
    db = connect(db_path)
    return db.get(id=row_id).data
