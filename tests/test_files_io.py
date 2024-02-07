from pathlib import Path
import pytest

from textual.widgets._data_table import ColumnKey, RowKey

from texase.app import TEXASE
from texase.table import TexaseTable, get_column_labels

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
