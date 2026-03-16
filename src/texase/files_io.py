from pathlib import Path
from functools import lru_cache
from typing import Iterable

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Footer, Input, Label, Tree


def build_write_exts() -> set[str]:
    from ase.io.formats import ioformats
    ext_list = []
    for format in ioformats.values():
        # We are only interested in seeing files that we can append to
        # else just write the filename yourself
        if not format.single and format.can_append:
            if format.extensions:
                ext_list.extend(format.extensions)
            else:
                ext_list.append(format.name)
    return set([f".{ext}" for ext in ext_list])


@lru_cache(maxsize=1)
def get_write_exts() -> set[str]:
    return build_write_exts()


def build_read_extensions_and_globs() -> tuple[set[str], set[str]]:
    from ase.io.formats import ioformats
    ext_list = []
    glob_list = []
    for format in ioformats.values():
        if format.can_read:
            # prefer globs to extensions, this is only based on vasp IOFormat
            if format.globs:
                glob_list.extend(format.globs)
            elif format.extensions:
                ext_list.extend(format.extensions)
            else:
                ext_list.append(format.name)
    return set([f".{ext}" for ext in ext_list]), set(glob_list)


@lru_cache(maxsize=1)
def get_read_extensions_and_globs() -> tuple[set[str], set[str]]:
    return build_read_extensions_and_globs()


def filter_write_paths(paths: Iterable[Path]) -> list[Path]:
    write_exts = get_write_exts()
    return [path for path in paths if (path.suffix in write_exts or path.is_dir())]


def filter_read_paths(paths: Iterable[Path]) -> list[Path]:
    read_exts, read_globs = get_read_extensions_and_globs()
    allowed_paths = []
    for path in paths:
        if path.name.startswith("."):
            # Don't allow hidden files (on Unix defined as starting with a .)
            continue
        elif path.suffix in read_exts or path.is_dir():
            allowed_paths.append(path)
    for glob in read_globs:
        allowed_paths.extend(path.parent.glob(glob))
    return allowed_paths


class ASEWriteDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return filter_write_paths(paths)


class ASEReadDirectoryTree(DirectoryTree):
    BINDINGS = [
        Binding("left", "set_root_up", "Go up", show=False),
        Binding("right", "set_root_down", "Go down", show=False),
    ]

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return filter_read_paths(paths)

    def action_set_root_up(self) -> None:
        """If the root node is selected, set a new root node as the
        parent of the current root node."""
        if self.cursor_node is not None:
            if self.cursor_node.is_root:
                self.path = self.path.parent
            elif self.cursor_node.data.path.is_dir():
                self.select_node(self.cursor_node.parent)

    def action_set_root_down(self) -> None:
        """If a directory is selected, set it as the new root node."""
        if self.cursor_node is not None and self.cursor_node.data.path.is_dir():
            self.path = self.cursor_node.data.path
            self.select_node(self.root)


class FilesIOScreen(ModalScreen[bool]):
    """Screen with a question that can be answered yes or no."""

    BINDINGS = [
        Binding("ctrl+g", "cancel", "Cancel", show=False),
    ]

    def __init__(self, read: bool = True) -> None:
        self.read = read
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.read:
            yield Container(
                Label("Select a file to read from"),
                ASEReadDirectoryTree(Path(".").resolve()),
                FolderLabel("Current folder"),
                Input(),
            )
        else:
            yield Container(
                Label("Select a file to write to"),
                ASEWriteDirectoryTree(Path(".").resolve()),
                FolderLabel("Current folder"),
                Input(),
            )
        yield Footer()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        self.dismiss(Path(submitted.value))

    def on_directory_tree_file_selected(
        self, selected: DirectoryTree.FileSelected
    ) -> None:
        self.dismiss(selected.path)

    @on(Tree.NodeHighlighted)
    def set_input(self, event: Tree.NodeHighlighted) -> None:
        # Add a / to the end if it is a directory
        path = event.node.data.path
        str_path = str(path)
        if path.is_dir():
            str_path += "/"
        self.query_one(Input).value = str_path


class FolderLabel(Label): ...
