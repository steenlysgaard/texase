import pytest
from ase.db import connect
from texase.app import TEXASE
from texase.keys import Key, KeyBox
from texase.table import TexaseTable
from textual.coordinate import Coordinate
from textual.css.query import NoMatches

from .shared_info import check_that_water_were_added_to_small_db, user_dct, water_to_add


@pytest.mark.asyncio
async def test_update_of_db_add_row(loaded_app, db_path):
    app, pilot = loaded_app
    # Import a structure
    atoms = water_to_add()
    db = connect(db_path)
    db.write(atoms, key_value_pairs=atoms.info['key_value_pairs'])

    # Update
    await pilot.press("g")

    check_that_water_were_added_to_small_db(app)

@pytest.mark.asyncio
async def test_update_of_db_remove_row(loaded_app, db_path):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    # Get the db row id
    assert str(table.get_cell_at(Coordinate(0, 0))) == '1'

    # Delete a row
    db = connect(db_path)
    db.delete([1])

    # Update
    await pilot.press("g")

    assert len(table.rows) == 1
    assert str(table.get_cell_at(Coordinate(0, 0))) == '2'

    # Check that user keys exclusive to row 1 are removed
    keybox = app.query_one(KeyBox)
    for key in user_dct:
        assert key not in app.data.unused_columns()

        with pytest.raises(NoMatches):
            keybox.query_one(f"#key-{key}", Key)  # Will fail if not found
        
        
@pytest.mark.asyncio
async def test_update_of_db_update_row(app_with_cursor_on_str_key, db_path):
    app, pilot = app_with_cursor_on_str_key
    table = app.query_one(TexaseTable)

    # Update a kvp
    db = connect(db_path)
    ns = "new_string"
    db.update(id=2, str_key=ns)
        
    # Update
    await pilot.press("down", "g")
    
    assert table.get_cell_at(table.cursor_coordinate) == ns
    
    assert app.data.df['str_key'].tolist() == ['hav', ns]

@pytest.mark.asyncio
async def test_update_of_db_update_row_and_delete_kvp(app_with_cursor_on_str_key, db_path):
    app, pilot = app_with_cursor_on_str_key

    # Update a kvp
    db = connect(db_path)
    ns = "new_string"
    db.update(id=2, str_key=ns)
    
    # Delete a kvp
    db.update(id=1, delete_keys=['int_key'])

    # Update
    await pilot.press("g")
    
    # Check that int_key is no longer present in app.data.df
    assert 'int_key' not in app.data.df.columns
    
    keybox = app.query_one(KeyBox)
    assert "int_key" not in app.data.unused_columns()

    with pytest.raises(NoMatches):
        keybox.query_one("#key-int_key", Key)  # Will fail if not found
        

@pytest.mark.asyncio
async def test_update_of_db_add_delete_and_update(app_with_cursor_on_str_key, db_path):
    app, pilot = app_with_cursor_on_str_key
    table = app.query_one(TexaseTable)

    # Update a kvp
    db = connect(db_path)
    ni = 5
    db.update(id=2, int_key=ni)

    # Delete a row
    db.delete([1])
        
    atoms = water_to_add()
    db.write(atoms, key_value_pairs=atoms.info['key_value_pairs'])
    
    assert not app.data.is_df_up_to_date()

    # Update
    await pilot.press("g")
    
    # There should be 2 rows
    assert len(table.rows) == 2
    
    # Check that str_key is no longer present in app.data.df
    assert 'str_key' not in app.data.df.columns
    
    assert "str_key" not in app.data.unused_columns()
    assert "str_key" not in app.data.chosen_columns
    assert "str_key" not in table.columns

    keybox = app.query_one(KeyBox)
    with pytest.raises(NoMatches):
        keybox.query_one("#key-str_key", Key)  # Will fail if not found

    assert app.data.df['id'].tolist() == [2, 3]

    # Check that new user keys are imported, but not shown yet
    assert 'number1' in app.data.unused_columns()

    # Check that the new user key is shown in the KeyBox
    keybox.query_one("#key-number1", Key)  # Will fail if not found

    # Check that the table is populated with the correct data
    assert app.data.df['formula'].tolist()[-1] == 'H2O'
    # Check the second row (1) and formula column (3)
    # Print column names
    assert table.get_cell_at(Coordinate(1, 3)) == 'H2O'
    
    assert app.data.is_df_up_to_date()
