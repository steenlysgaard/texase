import pytest
from texase.help import HelpScreen


@pytest.mark.asyncio
@pytest.mark.parametrize("hide_help_key", ["?", "q", "ctrl+g"])
async def test_help(loaded_app, hide_help_key):
    app, pilot = loaded_app

    # Press D and then n to cancel
    await pilot.press("?")
    assert isinstance(app.screen, HelpScreen)

    await pilot.press(hide_help_key)

    assert not isinstance(app.screen, HelpScreen)
