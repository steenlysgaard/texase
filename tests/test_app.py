import pytest

from asetui.app import ASETUI

@pytest.mark.asyncio
async def test_start_app(db_path):
    app = ASETUI(path=db_path)
    async with app.run_test() as pilot:
        pass
