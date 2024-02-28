import pytest

from texase.app import TEXASE


@pytest.mark.asyncio
async def test_view(db_path):
    app = TEXASE(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:

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
