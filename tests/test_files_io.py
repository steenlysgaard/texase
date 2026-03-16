from pathlib import Path
import importlib
import sys

import pytest
from ase.io import read, write
from texase.table import TexaseTable

from .shared_info import (
    check_that_water_were_added_to_small_db,
    test_atoms,
    water_to_add,
)


@pytest.mark.asyncio
async def test_read_traj_file(loaded_app, tmp_path):
    app, pilot = loaded_app
    # Create a trajectory file
    atoms = water_to_add()
    fname = str(tmp_path / "test.traj")
    write(fname, atoms)

    # Import the trajectory file
    await pilot.press("i", "tab", "ctrl+u", *list(fname), "enter")

    check_that_water_were_added_to_small_db(app)


@pytest.mark.asyncio
async def test_read_bad_file(loaded_app, tmp_path):
    app, pilot = loaded_app
    table = app.query_one(TexaseTable)
    original_no_rows = len(table.rows.keys())

    # Create a file with nothing in it
    fname = str(tmp_path / "test.traj")
    Path(fname).touch()

    # Clear any possible notifications
    app.clear_notifications()

    # Import the trajectory file
    await pilot.press("i", "tab", "ctrl+u", *list(fname), "enter")

    # Check that the error message is displayed
    await pilot.pause()
    assert len(app._notifications) == 1

    assert len(table.rows.keys()) == original_no_rows


@pytest.mark.asyncio
async def test_write_traj_file(loaded_app, tmp_path):
    _, pilot = loaded_app
    fname = str(tmp_path / "test.traj")

    # Export a trajectory file of the first row
    await pilot.press("x", "tab", "ctrl+u", *list(fname), "enter")

    # Check that the file has been created
    assert Path(fname).exists()
    atoms = read(fname)

    assert atoms.get_chemical_symbols() == [test_atoms[0]]


@pytest.mark.asyncio
async def test_write_bad_file(loaded_app, tmp_path):
    app, pilot = loaded_app
    # Try to write a silly file
    fname = str(tmp_path / "foo.bar")

    # Clear any possible notifications
    app.clear_notifications()

    # Import the trajectory file
    await pilot.press("x", "tab", "ctrl+u", *list(fname), "enter")

    # Check that the error message is displayed
    await pilot.pause()
    assert len(app._notifications) == 1

    # Check that the file has not been created
    assert not Path(fname).exists()


def test_files_io_builders_are_lazy(monkeypatch, tmp_path):
    sys.modules.pop("texase.files_io", None)
    files_io = importlib.import_module("texase.files_io")

    write_calls = 0
    read_calls = 0

    def fake_build_write_exts() -> set[str]:
        nonlocal write_calls
        write_calls += 1
        return {".traj"}

    def fake_build_read_extensions_and_globs() -> tuple[set[str], set[str]]:
        nonlocal read_calls
        read_calls += 1
        return {".traj"}, set()

    monkeypatch.setattr(files_io, "build_write_exts", fake_build_write_exts)
    monkeypatch.setattr(
        files_io,
        "build_read_extensions_and_globs",
        fake_build_read_extensions_and_globs,
    )
    files_io.get_write_exts.cache_clear()
    files_io.get_read_extensions_and_globs.cache_clear()

    assert write_calls == 0
    assert read_calls == 0

    test_file = tmp_path / "test.traj"
    test_file.touch()

    assert files_io.filter_write_paths([test_file]) == [test_file]
    assert write_calls == 1
    assert files_io.filter_write_paths([test_file]) == [test_file]
    assert write_calls == 1

    assert files_io.filter_read_paths([test_file]) == [test_file]
    assert read_calls == 1
    assert files_io.filter_read_paths([test_file]) == [test_file]
    assert read_calls == 1
