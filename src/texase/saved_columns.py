import json
from pathlib import Path

from texase.cache_files import cache_dir


class SavedColumns:
    _columns_file_path: Path
    _files_and_columns: dict[str, list[str]]

    def __init__(self) -> None:
        self._columns_file_path = cache_dir() / "columns.json"
        self._files_and_columns = self._read_columns_file()

    def _read_columns_file(self) -> dict[str, list[str]]:
        if self._columns_file_path.exists():
            with self._columns_file_path.open("r") as f:
                return json.load(f)
        return {}

    def _write_columns_file(self) -> None:
        with self._columns_file_path.open("w") as f:
            json.dump(self._files_and_columns, f, indent=4)

    def __getitem__(self, key: str) -> list[str] | None:
        return self._files_and_columns.get(key)

    def __setitem__(self, key: str, value: list[str]) -> None:
        self._files_and_columns[key] = value
        self._write_columns_file()

    def __delitem__(self, key: str) -> None:
        del self._files_and_columns[key]
        self._write_columns_file()

    def __len__(self) -> int:
        return len(self._files_and_columns)

    def __str__(self) -> str:
        return str(self._files_and_columns)

    def __repr__(self) -> str:
        return repr(self._files_and_columns)
