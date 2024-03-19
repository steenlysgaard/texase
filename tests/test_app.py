import pytest

from textual.coordinate import Coordinate

from texase.app import TEXASE
from texase.data import Data
from texase.table import TexaseTable, get_column_labels

from .shared_info import test_atoms, user_dct


@pytest.mark.asyncio
async def test_start_app(loaded_app):
    app, _ = loaded_app
    assert isinstance(app.data, Data)
    # Test that table is populated
    table = app.query_one(TexaseTable)
    no_rows = len(table.rows.keys())
    assert no_rows == 2

    # Check that the table is populated with the correct data
    for i in range(no_rows):
        row_values = table.get_row_at(i)
        assert test_atoms[i] in row_values

    column_labels = [str(c.label) for c in table.columns.values()]
    assert "formula" in column_labels

    assert list(table.get_column_at(column_labels.index("formula"))) == test_atoms


@pytest.mark.asyncio
async def test_add_column(loaded_app):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    # Check status before adding
    assert not app.show_add_column_box
    assert "str_key" not in get_column_labels(table.columns)
    assert "str_key" not in app.data.chosen_columns

    await pilot.press("+")
    # Check that the column add box is visible
    assert app.show_add_column_box
    assert app.query_one("#add-column-box").display

    # Type one of the user columns and complete
    await pilot.press("s", "t", "r", "right", "enter")

    # Check that the column add box is not visible
    assert not app.show_add_column_box

    # Check that the column has been added
    assert "str_key" in get_column_labels(table.columns)
    assert "str_key" in app.data.chosen_columns


@pytest.mark.asyncio
async def test_remove_column(loaded_app):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    columns_init = get_column_labels(table.columns)
    assert "magmom" in columns_init
    assert "magmom" in app.data.chosen_columns

    magmom_index = columns_init.index("magmom")

    # Move to magmom column
    await pilot.press(*(magmom_index * ("right",)))
    assert table.cursor_column == magmom_index

    # Remove magmom column
    await pilot.press("-")
    assert "magmom" not in get_column_labels(table.columns)
    assert "magmom" not in app.data.chosen_columns


def check_row_ids(table: TexaseTable, row_ids: list):
    for i in range(len(row_ids)):
        assert int(str(table.get_row_at(i)[0])) == row_ids[i]


@pytest.mark.asyncio
async def test_sort_column(loaded_app):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    # Check status before sorting
    assert app.data.sort_columns == ["id"]
    assert not app.data.sort_reverse
    check_row_ids(table, [1, 2])

    await pilot.press("s")
    assert app.data.sort_columns == ["id"]
    assert app.data.sort_reverse
    check_row_ids(table, [2, 1])

    # Sort by formula
    formula_index = get_column_labels(table.columns).index("formula")
    await pilot.press(*(formula_index * ("right",)))
    await pilot.press("s")
    assert app.data.sort_columns == ["formula", "id"]
    assert not app.data.sort_reverse
    check_row_ids(table, [2, 1])

    # Sort with the mouse by clicking the id column header
    await pilot.click(
        selector=TexaseTable, offset=(5, 0)
    )  # The labels take 3 characters, id is next
    assert app.data.sort_columns == ["id", "formula"]
    check_row_ids(table, [1, 2])

@pytest.mark.asyncio
async def test_sort_then_add_column(loaded_app):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    await pilot.press("s", "+", *list("str_key"), "enter")

    col_idx = get_column_labels(table.columns).index("str_key")
    assert table.get_cell_at(Coordinate(1, col_idx)) == user_dct["str_key"]
    assert table.get_cell_at(Coordinate(0, col_idx)) == ""

@pytest.mark.asyncio
async def test_rows_to_act_on(loaded_app):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)

    # Nothing marked
    assert table.ids_to_act_on() == [1]

    # One marked, not the row we are on
    await pilot.press("space", "down")
    assert table.ids_to_act_on() == [1]

    # Two marked
    await pilot.press("space")
    assert sorted(table.ids_to_act_on()) == [1, 2]
        
        
