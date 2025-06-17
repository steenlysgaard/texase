import json
import os
from pathlib import Path

from platformdirs import user_cache_dir


class SavedColumns:
    def __init__(self):
        # allow env‐override; otherwise store in user config dir
        env_path = os.environ.get("TEXASE_COLUMNS_FILE")
        if env_path:
            self._columns_file_path = Path(env_path)
        else:
            cfg = Path(user_cache_dir("texase"))
            cfg.mkdir(parents=True, exist_ok=True)
            self._columns_file_path = cfg / "columns.json"
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
