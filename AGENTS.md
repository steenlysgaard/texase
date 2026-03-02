# Repository Guidelines

## Project Structure & Module Organization
- Core TUI code lives in `src/texase/`; `app.py` exposes the Typer entrypoint, `table.py` handles grid rendering, and `cache_files.py`/`data.py` manage ASE database access and caching. Styling is in `texase.tcss`.
- Tests sit in `tests/` and mirror the module layout (e.g., `tests/test_table.py` for `table.py`). Shared fixtures are in `tests/shared_info.py` and `tests/conftest.py`.
- Demo assets and sample databases (`demo.gif`, `example.db`, `big_test.db`, etc.) live at the repo root and can be used for local runs. Packaging metadata is managed via `pyproject.toml` and the `uv.lock` lockfile.

## Build, Test, and Development Commands
- Install with dev tools: `uv sync --group dev` (uses `uv.lock`). If `uv` is unavailable, `pip install -e .` plus manual installs of dev deps from `pyproject.toml` works.
- Run the app locally (after install): `uv run texase example.db` or `texase example.db`.
- Test suite: `uv run pytest` or `python -m pytest`. Run tests in parallel with `pytest -n auto`.
- Coverage pass: `uv run pytest --cov=texase --cov-report=term-missing`.
- Format before sending changes: `uv run black src tests`.

## Coding Style & Naming Conventions
- Python 3.9+ with src layout; use 4-space indents and type hints where practical.
- Keep functions/methods in `snake_case`, classes in `PascalCase`, and module-level constants in `UPPER_SNAKE_CASE`.
- Follow Textual patterns already in the codebase (widgets in `table.py`, dialogs in `input_screens.py`, styles in `texase.tcss`). Prefer pure functions for data transforms in `data.py` and `cache_files.py`.
- Run Black with default settings; avoid manual tweaks that fight the formatter.

## Testing Guidelines
- Add or update tests under `tests/` using `pytest`; name files `test_*.py` and functions `test_*`.
- Prefer small, deterministic fixtures; reuse shared helpers in `tests/shared_info.py`.
- For features that touch rendering or caching, add assertions alongside existing coverage in `test_table.py`, `test_view.py`, or `test_cache.py`. Maintain coverage by running the `--cov` target when possible.

## Commit & Pull Request Guidelines
- Use short, present-tense commit messages similar to the existing history (e.g., `add cache test`, `fix table sorting`). Include issue/PR refs when relevant.
- For PRs, include a concise summary, testing notes (`pytest`, coverage), and screenshots or recordings for TUI-visible changes.
- Keep changes scoped; prefer separate commits for refactors vs. behavior changes. Update `pyproject.toml`/`uv.lock` together if you bump versions.
