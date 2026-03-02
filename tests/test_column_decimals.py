import pytest
from texase.table import TexaseTable, get_column_labels
from textual.coordinate import Coordinate


def decimal_places(value: str) -> int:
    if "." not in value:
        return 0
    return len(value.split(".")[1])


@pytest.mark.asyncio
async def test_adjust_float_column_precision_with_keys(loaded_app):
    app, pilot = loaded_app
    table: TexaseTable = app.query_one(TexaseTable)

    labels = get_column_labels(table.columns)
    mass_index = labels.index("mass")
    table.cursor_coordinate = Coordinate(0, mass_index)

    before = str(table.get_cell_at(Coordinate(0, mass_index)))
    before_precision = app.data.get_float_precision("mass")

    await pilot.press(">")
    after_increase = str(table.get_cell_at(Coordinate(0, mass_index)))
    assert app.data.get_float_precision("mass") == before_precision + 1
    assert decimal_places(after_increase) == decimal_places(before) + 1

    await pilot.press("<")
    after_decrease = str(table.get_cell_at(Coordinate(0, mass_index)))
    assert app.data.get_float_precision("mass") == before_precision
    assert after_decrease == before


@pytest.mark.asyncio
async def test_adjust_scientific_notation_precision_with_keys(loaded_app):
    app, pilot = loaded_app
    table: TexaseTable = app.query_one(TexaseTable)

    await pilot.press("+", *list("float_key"), "enter")

    # Put a large float value in scientific notation with many decimals in row id=1.
    app.data.update_value(1, "float_key", 6.02214076e23)

    labels = get_column_labels(table.columns)
    float_key_index = labels.index("float_key")
    table.cursor_coordinate = Coordinate(0, float_key_index)
    table.update_column_values("float_key")

    before = str(table.get_cell_at(Coordinate(0, float_key_index)))
    assert before == "6.02e+23"

    await pilot.press(">")
    after_increase = str(table.get_cell_at(Coordinate(0, float_key_index)))
    assert after_increase == "6.022e+23"

    await pilot.press("<")
    after_decrease = str(table.get_cell_at(Coordinate(0, float_key_index)))
    assert after_decrease == "6.02e+23"
