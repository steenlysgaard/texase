import pytest
import pytest_asyncio
from ase.data import atomic_numbers
from texase.search import (
    check_escape_character,
    ready_for_regex_search,
    valid_regex,
)
from texase.table import TexaseTable, get_column_labels
from textual.coordinate import Coordinate


async def check_element_search(table, pilot, element):
    """Check that the cursor is on the correct row, and that the row
    id is correct.

    """
    await pilot.press("ctrl+s", *list(element), "enter")
    assert table.cursor_row == atomic_numbers[element] - 1
    assert str(table.get_cell_at(Coordinate(table.cursor_row, 0))) == str(
        atomic_numbers[element]
    )


# Create a fixture with no user column. So that searches doesn't take
# user names into account.
@pytest_asyncio.fixture
async def loaded_app_with_big_db_no_user(loaded_app_with_big_db):
    app, pilot = loaded_app_with_big_db
    table = app.query_one(TexaseTable)

    # Remove user column
    # Determine the index of the user column
    column_labels = get_column_labels(table.columns)
    idx = column_labels.index("user")
    # Move to user column
    await pilot.press(*(idx * ("right",)))
    # Remove user column
    await pilot.press("-")
    # Move back to the first column
    await pilot.press(*(idx * ("left",)))

    yield app, pilot, table


@pytest.mark.asyncio
async def test_search(loaded_app_with_big_db_no_user):
    app, pilot, table = loaded_app_with_big_db_no_user
    searchbox = app.query_one("#search-box")

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
async def test_next_and_previous(loaded_app_with_big_db_no_user):
    _, pilot, table = loaded_app_with_big_db_no_user
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
async def test_search_wrap(loaded_app_with_big_db_no_user):
    _, pilot, table = loaded_app_with_big_db_no_user
    await pilot.press("ctrl+s", "O")

    # First hit for O should be O
    assert table.cursor_row == 7

    await pilot.press("ctrl+s")
    # Then Os
    assert table.cursor_row == 75

    await pilot.press("ctrl+s")
    # Then back to O
    assert table.cursor_row == 7


@pytest.mark.asyncio
async def test_regex_search_init(loaded_app_with_big_db):
    _, pilot = loaded_app_with_big_db

    # Starting a regex search shouldn't fail
    await pilot.press("ctrl+s", "\\")
    await pilot.press("ctrl+g")
    await pilot.press("ctrl+s", "[")
    await pilot.press("ctrl+g")


@pytest.mark.asyncio
async def test_regex_search_elements_starting_with_C(loaded_app_with_big_db_no_user):
    _, pilot, table = loaded_app_with_big_db_no_user

    # Match elements that start with 'C'
    await pilot.press("ctrl+s", *list("^C"))

    # First hit for C should be C
    assert table.cursor_row == 5

    await pilot.press("ctrl+s")
    # Then Cl
    assert table.cursor_row == 16

    await pilot.press("ctrl+s")
    # Then Ca
    assert table.cursor_row == 19


@pytest.mark.asyncio
async def test_regex_search_elements_starting_with_vowel(
    loaded_app_with_big_db_no_user,
):
    _, pilot, table = loaded_app_with_big_db_no_user

    # Match elements that start with a vowel
    await pilot.press("ctrl+s", *list("^[AEIOU]"))

    # First hit should be O
    assert table.cursor_row == 7

    await pilot.press("ctrl+s")
    # Then Al
    assert table.cursor_row == 12

    await pilot.press("ctrl+s")
    # Then Ar
    assert table.cursor_row == 17

    await pilot.press("ctrl+s")
    # Then As
    assert table.cursor_row == 32


@pytest.mark.asyncio
async def test_regex_search_elements_r_second(loaded_app_with_big_db_no_user):
    _, pilot, table = loaded_app_with_big_db_no_user

    # Match elements that have 'r' as the second letter
    await pilot.press("ctrl+s", *list(".r"))

    # First hit should be Ar
    assert table.cursor_row == 17

    await pilot.press("ctrl+s")
    # Then Cr
    assert table.cursor_row == 23

    await pilot.press("ctrl+s")
    # Then Br
    assert table.cursor_row == 34


# Test cases for the valid_regex function
@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("^[a-zA-Z]+$", True),  # Valid regex for letters only
        ("\\d{2,4}", True),  # Valid regex for 2 to 4 digits
        ("(hello|world", False),  # Invalid regex, unclosed parenthesis
        ("[a-z", False),  # Invalid regex, unclosed bracket
        ("\\", False),  # Invalid regex, lone escape character
        ("[\\]]", True),  # Valid regex, escaped closing bracket
        ("(?P<name>[a-zA-Z]+)", True),  # Valid regex with named group
        ("*", False),  # Invalid regex, quantifier has nothing to quantify
    ],
)
def test_valid_regex(input_string, expected):
    assert valid_regex(input_string) == expected


# Test cases for the check_escape_character function
@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("This is a test string without escape", False),
        ("This is a test string with escape \\", True),
        ("This is a test string with multiple escapes \\\\ but last is not", False),
        ("\\", True),  # Edge case: only escape character
    ],
)
def test_check_escape_character(input_string, expected):
    assert check_escape_character(input_string) == expected


# Test cases for the ready_for_regex_search function
@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("This is a test string ready for regex search", True),
        ("This is a test string with unclosed ( parenthesis", False),
        ("This is a test string with escape at the end \\", False),
        ("This is a test string with both issues (\\", False),
        (
            "This is a test string with closed (parentheses) and no escape at the end",
            True,
        ),
        ("This is a test string with escaped parenthesis \\( and no unclosed", True),
    ],
)
def test_ready_for_regex_search(input_string, expected):
    assert ready_for_regex_search(input_string) == expected
