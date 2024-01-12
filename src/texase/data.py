from __future__ import annotations

import operator
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Tuple, Union, overload, Iterable, Dict
from functools import wraps

import numpy as np
import pandas as pd
from ase.db import connect
from ase.db.table import all_columns
from ase import Atoms
from textual.widgets import ListItem, Label
from textual._cache import LRUCache

from texase.saved_columns import SavedColumns
from texase.formatting import format_column, get_age_string, pbc_str_to_array

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
        cache_key = tuple(args)
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
    df: pd.DataFrame
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
        self._sort: np.ndarray = np.arange(len(self.df))
        # self._df_cache: LRUCache[int, pd.DataFrame] = LRUCache(maxsize=128)
        self._filter_mask_cache: LRUCache[tuple, np.ndarray] = LRUCache(maxsize=128)
        self._string_df_cache: LRUCache[tuple, pd.DataFrame] = LRUCache(maxsize=128)
        self._string_column_cache: LRUCache[tuple, pd.Series] = LRUCache(maxsize=128)

    def unused_columns(self) -> List[str]:
        """Returns a list of columns that are not used in the table.

        Go through all columns + self.user_keys and check if they are
        in self.chosen_columns

        """
        return [
            col
            for col in all_columns + self.user_keys
            if col not in self.chosen_columns
        ]

    @overload
    def update_value(
        self, ids: int, column: str, value: str | float | int | None
    ) -> None:
        ...

    @overload
    def update_value(
        self, ids: Iterable[int], column: str, value: str | float | int | None
    ) -> None:
        ...

    def update_value(self, ids, column, value) -> None:
        """Updates the value in the database and self.df

        ids: list of ids
        column: column name
        value: new value
        """
        # Test if ids is iterable
        try:
            iter(ids)
        except TypeError:
            ids = [ids]

        if value is None:
            self.update_in_db(ids, delete_keys=[column])
        else:
            self.update_in_db(ids, {column: value})

        # Update in self.df
        for row_id in ids:
            self.update_df(row_id, column, value)

        # Clear the caches
        self._string_df_cache.clear()
        self._remove_edited_column_from_caches(column)

    def update_in_db(self, row_ids: int | Iterable[int],
                     key_value_pairs: Dict[str, Any] = {},
                     data: dict | None = None,
                     delete_keys: list = []) -> None:
        """Update the row id(s) db with the given key value pairs and data"""
        try:
            iter(row_ids)  # type: ignore
        except TypeError:
            row_ids = [row_ids]  # type: ignore

        atoms = None
        with connect(self.db_path) as db:
            for idx in row_ids:
                atoms = None
                if key_value_pairs:
                    if 'pbc' in key_value_pairs:
                        # We need to remove pbc from key_value_pairs,
                        # thus first we copy the dict and then pop pbc
                        # from the copy
                        key_value_pairs = dict(key_value_pairs)
                        
                        # Get the atoms and modify directly
                        atoms = db.get_atoms(idx)
                        atoms.pbc = pbc_str_to_array(key_value_pairs.pop('pbc'))
                db.update(idx, atoms, **key_value_pairs,
                          delete_keys=delete_keys, data=data)
        
    def update_row(self, row_id: int, key_value_pairs: dict = {}, data: dict | None = None) -> None:
        """Update the row id db with the given key value pairs and data.

        It is assumed that only editable keys are passed in key_value_pairs."""
        
        delete_keys = []
        for key, value in key_value_pairs.items():
            self.update_df(row_id, key, value)
            # Create delete_keys with the keys in key_value_pairs that have None as value
            if value is None:
                delete_keys.append(key)
        # Remove the keys in key_value_pairs that are going to be deleted
        for key in delete_keys:
            key_value_pairs.pop(key)
                
        self.update_in_db(row_id, key_value_pairs, data, delete_keys=delete_keys)
        
    def update_df(self, row_id: int, column: str, value: str | float | int | None) -> None:
        if value is None:
            value = pd.NaT
        self.df.loc[self.index_from_row_id(row_id), column] = value
                
    def index_from_row_id(self, row_id) -> int:
        return self.df.loc[self.df["id"] == row_id].index[0]

    def _remove_edited_column_from_caches(self, column) -> None:
        self._string_column_cache.discard((column,))
        for key in self._filter_mask_cache.keys():
            if column in key:
                self._filter_mask_cache.discard(key)

    def df_for_print(self) -> pd.DataFrame:
        """Returns the final dataframe after applying all filters and current sort."""
        df = self.string_df()
        return apply_filter_and_sort_on_df(df, self.filter_mask, self._sort)

    def column_for_print(self, column):
        """Get a string representation of a column in the DataFrame
        including filters and sorting."""
        col = self._string_column(column)
        return col.iloc[self._sort].iloc[self.filter_mask[self._sort]]

    def row_details(self, row_id: int) -> Tuple[dict, dict]:
        """Returns key value pairs from the row in two dictionaries:

        Static and editable key value pairs.
        All user keys and pbc are editable.
        """
        static_kvps = {}
        dynamic_kvps = {}
        editable_keys = self.user_keys + ["pbc"]
        for key, value in (
            self.df.loc[self.df["id"] == row_id].squeeze().dropna().items()
        ):
            if key in editable_keys:
                dynamic_kvps[key] = value
            else:
                static_kvps[key] = value
        return static_kvps, dynamic_kvps

    def row_data(self, row_id: int) -> list:
        dynamic_data = []
        for key, value in get_data(self.db_path, row_id).items():
            dynamic_data.append(ListItem(Label(f"[bold]{key}: [/bold]{value}")))
        return dynamic_data

    def get_atoms(self, row) -> Atoms:
        db = connect(self.db_path)
        return db.get_atoms(id=row)

    def can_column_be_added(self, column) -> bool:
        """Check if a column can be added to the table, i.e. is it
        present in the data but not in the table."""
        return column in self.unused_columns()
    
    def add_to_chosen_columns(self, column) -> None:
        """Add a column to the table.

        Before calling this function it is checked that the column is valid.
        """
        self.chosen_columns.append(column)

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
        df = self.df_for_print()
        mask = np.column_stack(
            [
                df[col].astype(str).str.contains(search_string, na=False)
                for col in self.chosen_columns
            ]
        )
        return zip(*mask.nonzero())

    def sort(self, columns: list, reverse: bool) -> np.ndarray:
        """Set the indices to sort self.df in self._sort. Return the sorted ids."""
        df = self.df
        self._sort = df.sort_values(columns, ascending=not reverse).index.to_numpy()
        return self.id_array_with_filter_and_sort()

    def id_array_with_filter_and_sort(
        self, filter_mask: np.ndarray | None = None
    ) -> np.ndarray:
        """Returns an array of ids after applying filters and sorting."""
        if filter_mask is None:
            filter_mask = self.filter_mask
        return apply_filter_and_sort_on_df(self.df, filter_mask, self._sort)[
            "id"
        ].to_numpy()

    @property
    def filter_mask(self) -> np.ndarray:
        """Combine all boolean arrays from the filters into one."""
        mask = np.ones(len(self.df), dtype=bool)
        for filter in self._filters:
            mask &= self._filter_mask(filter)
        return mask

    @cache
    def _filter_mask(self, filter: tuple) -> np.ndarray:
        """Returns a boolean array of indices that pass the filter"""
        filter_key, op, filter_value = filter
        mask = ops[op](self.df[filter_key], operator_type_conversion[op](filter_value))
        return mask.to_numpy()

    def add_filter(self, key, operator, value) -> None:
        # We get the value as a string. Maybe we should convert it to
        # the correct type if the column values are not strings? But
        # how do we know? We try to deduce from the operator

        self._filters += ((key, operator, value),)

    def remove_filter(self, filter_tuple: Tuple[str, str, str]) -> None:
        self._filters = tuple(
            filter for filter in self._filters if filter != filter_tuple
        )

    def string_df(self) -> pd.DataFrame:
        return self._string_df(tuple(self.chosen_columns))

    @cache
    def _string_df(self, chosen_columns) -> pd.DataFrame:
        """Get a representation of the DataFrame where all values are strings.

        This is used for displaying the data in the table. The
        function depends on self.chosen_columns. The result is cached
        in self._string_df_cache. Thus the cache key will be built
        with self.chosen_columns.

        """
        df_list = []
        for column in chosen_columns:
            df_list.append(self._string_column(column))
        return pd.concat(df_list, axis=1).fillna("", axis=1)

    # def get_df(self, filters: tuple | None = None) -> pd.DataFrame:
    #     if filters is None:
    #         return self._df(self._filters)
    #     return self._df(filters)

    # @cache
    # def _df(self, filters: tuple = ()) -> pd.DataFrame:
    #     df = self.df
    #     for filter_key, op, filter_value in filters:
    #         df = df[ops[op](df[filter_key], operator_type_conversion[op](filter_value))]
    #     return df

    def get_mask_of_df_with_filter(
        self, filter_tuple: Tuple[str, str, str]
    ) -> np.ndarray:
        return self._filter_mask(filter_tuple)

    @cache
    def _string_column(self, column: str) -> pd.Series:
        """Get a string representation of a column in the raw
        DataFrame without filters or sorting."""
        df = self.df
        column_data = df[column]
        if column == "age":
            column_data = format_column(column_data, format_function=get_age_string)
        return format_column(column_data)


def apply_filter_and_sort_on_df(
    df: pd.DataFrame, filter_mask: np.ndarray, sort: np.ndarray
) -> pd.DataFrame:
    """Apply filter mask and sorting indices on a DataFrame. Return the result.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to be filtered and sorted.
    filter_mask : np.ndarray
        A boolean array of the same length as the DataFrame's index, indicating which rows to keep.
    sort : np.ndarray
        An array of integers of the same length as the DataFrame's index, indicating the order of the rows.

    Returns
    -------
    pd.DataFrame
        The filtered and sorted DataFrame.

    Examples
    --------
    >>> df = pd.DataFrame({'name': ['Alice', 'Bob', 'Charlie', 'David'], 'age': [25, 30, 35, 40]})
    >>> filter_mask = np.array([True, False, True, False])
    >>> sort = np.array([2, 0, 3, 1])
    >>> apply_filter_and_sort_on_df(df, filter_mask, sort)
          name  age
    2  Charlie   35
    0    Alice   25
    """
    return df.iloc[sort].iloc[filter_mask[sort]]


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
    df = pd.DataFrame(cols)
    # df = pd.DataFrame(cols, index=cols["id"])
    df["id"] = df["id"].astype("int")
    return df, list(user_keys)




def get_value(row, key) -> str:
    """Get the value from the row to the dataframe."""
    if key == "age":
        # value = float_to_time_string(now() - row.ctime)
        value = row.ctime
    elif key == "pbc":
        # Convert pbc to a string of F and T because we don't want
        # to save arrays in the df
        value = "".join("FT"[int(p)] for p in row.pbc)
    else:
        value = row.get(key, pd.NaT)
    return value


def get_data(db_path, row_id):
    db = connect(db_path)
    return db.get(id=row_id).data

