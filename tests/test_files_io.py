from pathlib import Path
import pytest

from textual.coordinate import Coordinate

from texase.app import TEXASE
from texase.table import TexaseTable

from ase.io import write
from ase import Atoms


@pytest.mark.asyncio
async def test_read_traj_file(db_path, tmp_path):
    app = TEXASE(path=db_path)
    async with app.run_test(size=(200, 50)) as pilot:
        table = app.query_one(TexaseTable)

        # Create a trajectory file
        atoms = Atoms('H2O')
        atoms.info['key_value_pairs'] = {'number1': 58}
        fname = str(tmp_path / 'test.traj')
        write(fname, atoms)
        
        # Import the trajectory file
        await pilot.press("i", "tab", "ctrl+u", *list(fname), "enter")

        assert len(table.rows) == 3
        
        # Check that the table is populated with the correct data
        assert app.data.df['formula'].tolist()[-1] == 'H2O'
        # Check the third row (2) and formula column (3)
        assert table.get_cell_at(Coordinate(2, 3)) == 'H2O'


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

        
