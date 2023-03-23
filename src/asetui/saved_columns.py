import json
import os
from pathlib import Path


class SavedColumns:
    def __init__(self):
        self._columns_file_path = Path(
            os.environ.get("ASETUI_COLUMNS_FILE", Path.home() / ".asetui-columns.json")
        )
        self._files_and_columns = self._read_columns_file()

    def _read_columns_file(self):
        if self._columns_file_path.exists():
            with self._columns_file_path.open("r") as f:
                return json.load(f)
        return {}

    def _write_columns_file(self):
        with self._columns_file_path.open("w") as f:
            json.dump(self._files_and_columns, f, indent=4)

    def __getitem__(self, key):
        return self._files_and_columns.get(key, None)

    def __setitem__(self, key, value):
        self._files_and_columns[key] = value
        self._write_columns_file()

    def __delitem__(self, key):
        del self._files_and_columns[key]
        self._write_columns_file()

    def __len__(self):
        return len(self._files_and_columns)

    def __str__(self):
        return str(self._files_and_columns)

    def __repr__(self):
        return repr(self._files_and_columns)
