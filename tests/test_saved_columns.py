import json
import os
from pathlib import Path

from texase.cache_files import columns_file
from texase.saved_columns import SavedColumns


def test_saved_columns(tmp_path: Path):
    os.environ["TEXASE_CACHE_DIR"] = str(tmp_path)
    columns_file_path = columns_file()
    # create an instance of SavedColumns
    saved_columns = SavedColumns()
    # test the __init__ method
    assert saved_columns._columns_file_path == columns_file_path
    assert saved_columns._files_and_columns == {}
    # test the __getitem__ method
    assert saved_columns["foo"] is None
    # test the __setitem__ method
    saved_columns["foo"] = ["bar", "baz"]
    assert saved_columns["foo"] == ["bar", "baz"]
    # test the __delitem__ method
    del saved_columns["foo"]
    assert saved_columns["foo"] is None
    # test the __len__ method
    assert len(saved_columns) == 0
    # test the __str__ method
    assert str(saved_columns) == "{}"
    # test the __repr__ method
    assert repr(saved_columns) == "{}"


def test_read_and_write_saved_columns(tmp_path: Path):
    os.environ["TEXASE_CACHE_DIR"] = str(tmp_path)
    columns_file_path = columns_file()
    # create an instance of SavedColumns
    saved_columns = SavedColumns()
    # test the _read_columns_file method
    assert saved_columns._read_columns_file() == {}
    # write some data to the file
    saved_columns["foo"] = ["bar", "baz"]
    # test the _read_columns_file method again
    assert saved_columns._read_columns_file() == {"foo": ["bar", "baz"]}
    # test the _write_columns_file method
    saved_columns["bar"] = ["qux", "quux"]
    with columns_file_path.open("r") as f:
        assert json.load(f) == {"foo": ["bar", "baz"], "bar": ["qux", "quux"]}
