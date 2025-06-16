import pytest
from texase.table import TexaseTable
from textual.widgets._data_table import RowKey


@pytest.mark.asyncio
async def test_mark_row(loaded_app):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    assert not table.marked_rows

    # Mark the first row
    await pilot.press("space")
    assert table.marked_rows == {RowKey("1")}

    # Mark the second row
    await pilot.press("space")
    assert table.marked_rows == {RowKey("1"), RowKey("2")}

    # Unmark the first row
    await pilot.press("up", "space")
    assert table.marked_rows == {RowKey("2")}

    # Unmark all rows
    await pilot.press("U")
    assert not table.marked_rows

    # Mark the first row
    await pilot.press("up", "space")
    assert table.marked_rows == {RowKey("1")}

    # Unmark with u
    await pilot.press("up", "u")
    assert not table.marked_rows

    # Mark with the mouse
    response = await pilot.click(TexaseTable, offset=(1, 2))
    assert response
    assert table.marked_rows == {RowKey("2")}
