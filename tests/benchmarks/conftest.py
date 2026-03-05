import os
from pathlib import Path

import numpy as np
import pytest
from ase import Atoms
from ase.data import chemical_symbols
from ase.db import connect

BENCHMARK_SIZES = {
    "small": 100,
    "medium": 10_000,
    "large": 100_000,
}
BENCH_DB_DIR = Path(__file__).resolve().parents[2] / ".benchmarks" / "db"


def _create_benchmark_db(path: Path, rows: int, seed: int = 7) -> None:
    rng = np.random.default_rng(seed)
    with connect(path) as db:
        for i in range(rows):
            symbol = chemical_symbols[(i % 20) + 1]
            atoms = Atoms(
                symbol,
                cell=[5 + (i % 3), 5 + ((i + 1) % 3), 5 + ((i + 2) % 3)],
                pbc=[True, True, False],
            )
            key_value_pairs = {
                "str_key": f"group-{i % 50}",
                "int_key": i % 10_000,
                "float_key": float(i) / 13.0,
                "bool_key": (i % 2) == 0,
            }
            if i % 3 == 0:
                key_value_pairs["sparse_float"] = float(rng.normal())
            if i % 10 == 0:
                key_value_pairs["tag"] = f"tag-{i % 200}"
            db.write(atoms, key_value_pairs=key_value_pairs)


@pytest.fixture(scope="session")
def benchmark_size() -> str:
    size = os.environ.get("TEXASE_BENCHMARK_SIZE", "medium")
    if size not in BENCHMARK_SIZES:
        raise ValueError(
            f"Invalid TEXASE_BENCHMARK_SIZE={size!r}. "
            f"Choose one of: {', '.join(BENCHMARK_SIZES)}"
        )
    return size


@pytest.fixture(scope="session")
def benchmark_rows(benchmark_size: str) -> int:
    return BENCHMARK_SIZES[benchmark_size]


@pytest.fixture(scope="session")
def benchmark_db_path(
    benchmark_rows: int, benchmark_size: str
) -> Path:
    BENCH_DB_DIR.mkdir(parents=True, exist_ok=True)
    db_path = BENCH_DB_DIR / f"benchmark_{benchmark_size}.db"
    if not db_path.exists():
        _create_benchmark_db(db_path, rows=benchmark_rows)
    return db_path
