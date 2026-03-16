import asyncio
import threading

import pytest
from texase.app import TEXASE
from texase.data import Data
from texase.table import TexaseTable


@pytest.mark.asyncio
async def test_initial_load_then_async_remaining_rows(over_100_db_path, monkeypatch):
    remaining_rows_started = threading.Event()
    release_remaining_rows = threading.Event()

    original_add_remaining_rows = Data.add_remaining_rows_to_df

    def add_remaining_rows_with_gate(self):
        remaining_rows_started.set()
        # Ensure we can inspect the initial 100-row state before async completion.
        release_remaining_rows.wait(timeout=5)
        return original_add_remaining_rows(self)

    monkeypatch.setattr(
        Data, "add_remaining_rows_to_df", add_remaining_rows_with_gate, raising=True
    )

    app = TEXASE(path=over_100_db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        started = await asyncio.to_thread(remaining_rows_started.wait, 3)
        assert started

        table = app.query_one(TexaseTable)
        assert len(table.rows) == 100

        release_remaining_rows.set()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert len(table.rows) == 150
