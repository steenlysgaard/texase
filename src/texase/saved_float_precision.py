import json
from pathlib import Path

from texase.cache_files import float_precision_file


class SavedFloatPrecision:
    _precision_file_path: Path
    _files_and_precision: dict[str, dict[str, int]]

    def __init__(self) -> None:
        self._precision_file_path = float_precision_file()
        self._files_and_precision = self._read_precision_file()

    def _read_precision_file(self) -> dict[str, dict[str, int]]:
        if self._precision_file_path.exists():
            with self._precision_file_path.open("r") as f:
                return json.load(f)
        return {}

    def _write_precision_file(self) -> None:
        with self._precision_file_path.open("w") as f:
            json.dump(self._files_and_precision, f, indent=4)

    def __getitem__(self, key: str) -> dict[str, int] | None:
        return self._files_and_precision.get(key)

    def __setitem__(self, key: str, value: dict[str, int]) -> None:
        self._files_and_precision[key] = value
        self._write_precision_file()

    def __delitem__(self, key: str) -> None:
        del self._files_and_precision[key]
        self._write_precision_file()

    def __len__(self) -> int:
        return len(self._files_and_precision)

    def __str__(self) -> str:
        return str(self._files_and_precision)

    def __repr__(self) -> str:
        return repr(self._files_and_precision)
