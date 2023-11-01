import os
import json
from asetui.saved_columns import SavedColumns

def test_saved_columns(tmp_path):
    # create a temporary file for testing
    columns_file_path = tmp_path / "columns.json"
    os.environ["ASETUI_COLUMNS_FILE"] = str(columns_file_path)
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

def test_read_and_write_saved_columns(tmp_path):
    # create a temporary file for testing
    columns_file_path = tmp_path / "columns.json"
    os.environ["ASETUI_COLUMNS_FILE"] = str(columns_file_path)
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
    
