import asyncio
import os

import pytest

from texase.app import TEXASE
from texase.table import TexaseTable

if os.environ.get("TEXASE_RUN_BENCHMARKS") != "1":
    pytest.skip(
        "Benchmarks are opt-in. Set TEXASE_RUN_BENCHMARKS=1 to run them.",
        allow_module_level=True,
    )

pytest.importorskip("pytest_benchmark")


@pytest.mark.benchmark(group="tui")
@pytest.mark.benchmark(min_rounds=3, max_time=6)
def test_benchmark_tui_startup_table_build(
    benchmark, benchmark_db_path, benchmark_rows
):
    def run_once() -> None:
        async def launch_app() -> None:
            app = TEXASE(path=str(benchmark_db_path))
            async with app.run_test(size=(200, 50)) as pilot:
                await app.workers.wait_for_complete()
                # Flush pending UI messages so table rows are fully updated.
                await pilot.pause()
                table = app.query_one(TexaseTable)
                assert len(table.rows) == benchmark_rows

        asyncio.run(launch_app())

    benchmark.pedantic(run_once, iterations=1, rounds=3)
