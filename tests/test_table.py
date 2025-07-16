import pytest
from texase.table import TexaseTable, get_column_labels, list_formatter, re_range
from textual.coordinate import Coordinate


def get_column_index(table: TexaseTable, column_name: str) -> int:
    """Get the index of a column by its name."""
    labels = get_column_labels(table.columns)
    if column_name not in labels:
        raise ValueError(f"Column '{column_name}' not found in table columns.")
    return labels.index(column_name)


@pytest.mark.parametrize(
    "column,editable",
    [
        ("mass", False),
        ("pbc", True),
    ],
)
@pytest.mark.asyncio
async def test_table_is_cell_editable(loaded_app, column, editable):
    app, _ = loaded_app
    table: TexaseTable = app.query_one(TexaseTable)

    column_index = get_column_index(table, column)

    table.cursor_coordinate = Coordinate(0, column_index)

    editable = table.is_cell_editable()
    assert editable is editable


@pytest.mark.asyncio
async def test_update_row_editable_cells_updates_cells(loaded_app):
    """update_row_editable_cells() should update only existing columns on the current row."""
    app, _ = loaded_app
    table: TexaseTable = app.query_one(TexaseTable)

    col_idx = get_column_index(table, "pbc")
    table.cursor_coordinate = Coordinate(1, col_idx)

    # Make an update dict that includes a nonexistent column too
    updates = {
        "pbc": "FTF",
        "this_column_does_not_exist": "SHOULD_BE_SKIPPED",
    }

    table.update_row_editable_cells(updates)

    # Assert only the two real columns changed
    cell1 = table.get_cell_at(Coordinate(table.cursor_row, col_idx))
    assert str(cell1) == "FTF"


# Tests for list_formatter(start, end, step)
@pytest.mark.parametrize(
    "start,end,step,expected",
    [
        (1, 4, 1, "1-4"),
        (5, 5, 1, "5-5"),
        (2, 10, 2, "2-10:2"),
        (7, 9, 2, "7-9:2"),
    ],
)
def test_list_formatter(start, end, step, expected):
    assert list_formatter(start, end, step) == expected


# Tests for re_range(lst)
@pytest.mark.parametrize(
    "input_list,expected",
    [
        ([1], "1"),
        ([1, 2], "1,2"),
        ([1, 2, 3], "1-3"),
        ([1, 2, 3, 4, 6, 8], "1-4,6,8"),
        ([1, 3, 5, 7], "1-7:2"),
        ([1, 2, 4, 5, 7], "1,2,4,5,7"),
        ([2, 4, 7, 10, 13], "2,4-13:3"),
        ([10, 8, 6, 4], "10-4:-2"),  # re_range doesn't sort
    ],
)
def test_re_range(input_list: list, expected: str):
    # Ensure original order doesn't matter
    output = re_range(input_list)
    assert output == expected
