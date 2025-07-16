import os
import time
from pathlib import Path

import pandas as pd
import pytest
from texase.cache_files import save_df_cache_file
from texase.data import (
    COLUMN_DTYPES,
    db_last_modified,
    instantiate_data,
    is_cache_valid,
    recommend_dtype,
)


def test_db_last_modified_file(tmp_path: Path):
    # Create an empty "db" file and record its mtime
    db_file = tmp_path / "test.db"
    db_file.write_text("")  # touch
    mtime = db_file.stat().st_mtime

    # Should return almost the same timestamp
    ts = db_last_modified(db_file)
    assert isinstance(ts, type(time.localtime())) or hasattr(ts, "timestamp")
    assert abs(ts.timestamp() - mtime) < 1e-3

    # Nonexistent path should raise NotImplementedError
    with pytest.raises(NotImplementedError):
        db_last_modified(tmp_path / "no_such.db")


def test_is_cache_valid(tmp_path: Path):
    db_file = tmp_path / "db.sqlite"
    db_file.write_text("")

    cache_file = tmp_path / "cache.parquet"
    # write a simple df to parquet
    pd.DataFrame({"a": [1, 2, 3]}).to_parquet(cache_file)
    # ensure cache is newer
    now = time.time()
    os.utime(db_file, (now - 100, now - 100))
    os.utime(cache_file, (now, now))

    assert is_cache_valid(db_file, cache_file) is True

    # make cache older than db
    os.utime(cache_file, (now - 200, now - 200))
    assert is_cache_valid(db_file, cache_file) is False

    # if db “backend” not a file, is_cache_valid should quietly return False
    bogus_db = tmp_path / "no_db"
    assert is_cache_valid(bogus_db, cache_file) is False


def test_instantiate_data_reads_parquet(tmp_path: Path):
    # First set the tmp_path as the TEXASE_CACHE_DIR env var
    os.environ["TEXASE_CACHE_DIR"] = str(tmp_path)

    # simulate a "db" file and a valid cache.parquet next to it
    db_file = tmp_path / "my.db"
    db_file.write_text("")

    # create a DataFrame with extra user-key columns
    dct = {
        "id": [10, 20],
        "energy": [0.1, 0.2],
        "mykey": ["x", "y"],
        "float_int": [10, 0.1],
        "bool_int": [10, True],
        "str_bool": [True, "yes"],
        "str_int": [3, "yes"],
        "str_float": [3.5, "yes"],
        "bool_bool": [True, False],
    }
    cols = {}
    for k, v in dct.items():
        dtype = COLUMN_DTYPES.get(k, recommend_dtype(v))
        cols[k] = pd.Series(v, dtype=dtype)

    df = pd.DataFrame(cols)

    save_df_cache_file(df, db_file)

    # call with use_cache=True so we hit parquet
    data = instantiate_data(
        db_path=str(db_file),
        sel="",
        limit=None,
        use_cache=True,
    )

    # 1) Columns match exactly
    assert set(data.df.columns) == set(df.columns)

    # 2) Content matches (ignore the index)
    pd.testing.assert_frame_equal(
        df.reset_index(drop=True),
        data.df.reset_index(drop=True),
        check_dtype=True,
        check_column_type=True,
        check_like=True,
    )

    # 3) And the extra column showed up as a user_key
    assert "mykey" in data.user_keys
