import pytest

from texase.app import TEXASE

@pytest.mark.filterwarnings('ignore:Not all images have the same boundary conditions!')
@pytest.mark.asyncio
async def test_view(loaded_app):
    app, pilot = loaded_app

    # View first row
    await pilot.press("v")

    assert app.gui.window.exists

    assert len(app.gui.images) == 1
    assert len(app.gui.images[0]) == 1

    # Close window
    app.gui.exit()

    assert not app.gui.window.exists

    # Mark both rows and then view
    await pilot.press("space", "space", "v")

    assert app.gui.window.exists

    assert len(app.gui.images) == 2

    app.gui.exit()
