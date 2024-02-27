from pathlib import Path
import pytest

from texase.app import TEXASE
from texase.table import TexaseTable

from ase.io import write, read

from .shared_info import test_atoms, water_to_add, check_that_water_were_added_to_small_db


@pytest.mark.asyncio
async def test_read_traj_file(db_path, tmp_path):
    app = TEXASE(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        # Create a trajectory file
        atoms = water_to_add()
        fname = str(tmp_path / 'test.traj')
        write(fname, atoms)
        
        # Import the trajectory file
        await pilot.press("i", "tab", "ctrl+u", *list(fname), "enter")
        
        check_that_water_were_added_to_small_db(app)


@pytest.mark.asyncio
async def test_read_bad_file(db_path, tmp_path):
    app = TEXASE(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(TexaseTable)
        original_no_rows = len(table.rows.keys())
        
        # Create a file with nothing in it
        fname = str(tmp_path / 'test.traj')
        Path(fname).touch()
        
        # Check that no error messages are displayed
        assert len(app._notifications) == 0
        
        # Import the trajectory file
        await pilot.press("i", "tab", "ctrl+u", *list(fname), "enter")
        
        # Check that the error message is displayed
        await pilot.pause()
        assert len(app._notifications) == 1

        assert len(table.rows.keys()) == original_no_rows

        
@pytest.mark.asyncio
async def test_write_traj_file(db_path, tmp_path):
    app = TEXASE(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        fname = str(tmp_path / 'test.traj')
        
        # Export a trajectory file of the first row
        await pilot.press("x", "tab", "ctrl+u", *list(fname), "enter")
        
        # Check that the file has been created
        assert Path(fname).exists()
        atoms = read(fname)
        
        assert atoms.get_chemical_symbols() == [test_atoms[0]]

@pytest.mark.asyncio
async def test_write_bad_file(db_path, tmp_path):
    app = TEXASE(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        # Try to write a silly file
        fname = str(tmp_path / 'foo.bar')
        
        # Check that no error messages are displayed
        assert len(app._notifications) == 0
        
        # Import the trajectory file
        await pilot.press("x", "tab", "ctrl+u", *list(fname), "enter")
        
        # Check that the error message is displayed
        await pilot.pause()
        assert len(app._notifications) == 1
        
        # Check that the file has not been created
        assert not Path(fname).exists()
