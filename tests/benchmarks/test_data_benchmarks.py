import os

import pytest
from ase.db import connect

from texase.cache_files import save_df_cache_file
from texase.data import db_to_df, instantiate_data

if os.environ.get("TEXASE_RUN_BENCHMARKS") != "1":
    pytest.skip(
        "Benchmarks are opt-in. Set TEXASE_RUN_BENCHMARKS=1 to run them.",
        allow_module_level=True,
    )

pytest.importorskip("pytest_benchmark")


@pytest.mark.benchmark(group="data")
def test_benchmark_db_to_df(benchmark, benchmark_db_path):
    def run() -> None:
        with connect(benchmark_db_path) as db:
            db_to_df(db)

    benchmark(run)


@pytest.mark.benchmark(group="data")
def test_benchmark_instantiate_data_cold(benchmark, benchmark_db_path):
    benchmark(lambda: instantiate_data(db_path=str(benchmark_db_path), use_cache=False))


@pytest.mark.benchmark(group="data")
def test_benchmark_instantiate_data_cached(
    benchmark, benchmark_db_path, tmp_path, monkeypatch
):
    monkeypatch.setenv("TEXASE_CACHE_DIR", str(tmp_path))

    with connect(benchmark_db_path) as db:
        df, _ = db_to_df(db)
    save_df_cache_file(df, benchmark_db_path)

    benchmark(lambda: instantiate_data(db_path=str(benchmark_db_path), use_cache=True))


@pytest.mark.benchmark(group="data")
def test_benchmark_string_df_generation(benchmark, benchmark_db_path):
    data = instantiate_data(db_path=str(benchmark_db_path), use_cache=False)

    def run() -> None:
        data.clear_all_caches()
        data.string_df()

    benchmark(run)


@pytest.mark.benchmark(group="data")
def test_benchmark_sort_int_column(benchmark, benchmark_db_path):
    data = instantiate_data(db_path=str(benchmark_db_path), use_cache=False)

    def run() -> None:
        data.sort_columns = ["id"]
        data.sort_reverse = False
        data.sort("int_key")

    benchmark(run)


@pytest.mark.benchmark(group="data")
def test_benchmark_filter_and_sort_for_print(benchmark, benchmark_db_path):
    data = instantiate_data(db_path=str(benchmark_db_path), use_cache=False)

    def run() -> None:
        data.clear_all_caches()
        data._filters = tuple()
        data.add_filter("int_key", ">=", "500")
        data.add_filter("bool_key", "==", "True")
        data.df_for_print()

    benchmark(run)
