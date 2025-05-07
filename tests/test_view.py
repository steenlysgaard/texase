import pytest


@pytest.mark.filterwarnings("ignore:Not all images have the same boundary conditions!")
@pytest.mark.asyncio
async def test_view(loaded_app):
    app, pilot = loaded_app
    table = app.query_one("TexaseTable")

    # View first row
    await pilot.press("v")

    assert table.gui.window.exists

    assert len(table.gui.images) == 1
    assert len(table.gui.images[0]) == 1

    # Close window
    table.gui.exit()

    assert not table.gui.window.exists

    # Mark both rows and then view
    await pilot.press("space", "space", "v")

    assert table.gui.window.exists

    assert len(table.gui.images) == 2

    table.gui.exit()
