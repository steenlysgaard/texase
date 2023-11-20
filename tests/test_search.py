import pytest

from textual.coordinate import Coordinate

from ase.data import atomic_numbers

from asetui.app import ASETUI
from asetui.table import AsetuiTable


async def check_element_search(table, pilot, element):
    """Check that the cursor is on the correct row, and that the row
    id is correct.

    """
    await pilot.press("ctrl+s", *list(element), "enter")
    assert table.cursor_row == atomic_numbers[element] - 1
    assert str(table.get_cell_at(Coordinate(table.cursor_row, 0))) == str(
        atomic_numbers[element]
    )


@pytest.mark.asyncio
async def test_search(big_db_path):
    app = ASETUI(path=big_db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        searchbox = app.query_one("#search-box")
        table = app.query_one(AsetuiTable)

        # Check status before adding filter
        assert not app.show_search_box
        assert not searchbox.display

        await pilot.press("ctrl+s")

        # Check status after adding filter
        assert app.show_search_box
        assert searchbox.display
        
        # No element starts with Q so cursor should stay
        # at the same position
        await pilot.press("Q")
        assert table.cursor_column == 0
        assert table.cursor_row == 0
        await pilot.press("enter")
        assert table.cursor_column == 0
        assert table.cursor_row == 0
        
        await pilot.press("ctrl+s")

        # Search for Ar and check that the search box is not visible
        await pilot.press("A", "r", "enter")
        assert not app.show_search_box
        assert not searchbox.display

        # The selected row should be 17 since Ar is the 18th element
        # in the periodic table and the table is 0-indexed
        assert table.cursor_row == 17

        # The row id, however, should be 18
        assert str(table.get_cell_at(Coordinate(table.cursor_row, 0))) == "18"

        # Check some elements
        for element in ["Li", "Au", "Es"]:
            await check_element_search(table, pilot, element)


@pytest.mark.asyncio
async def test_next_and_previous(big_db_path):
    app = ASETUI(path=big_db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(AsetuiTable)
        await pilot.press("ctrl+s", "S")

        # First hit for S should be Si
        assert table.cursor_row == 13

        await pilot.press("ctrl+s")
        # Then S
        assert table.cursor_row == 15

        await pilot.press("ctrl+s")
        # Then Sc
        assert table.cursor_row == 20

        await pilot.press("ctrl+r")
        # Back to S
        assert table.cursor_row == 15


@pytest.mark.asyncio
async def test_search_wrap(big_db_path):
    app = ASETUI(path=big_db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(AsetuiTable)
        await pilot.press("ctrl+s", "O")

        # First hit for O should be O
        assert table.cursor_row == 7
        
        await pilot.press("ctrl+s")
        # Then Os
        assert table.cursor_row == 75

        await pilot.press("ctrl+s")
        # Then back to O
        assert table.cursor_row == 7
        
        
