from typing import Iterable
from pathlib import Path
from textual import on
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, Input, Tree
from textual.binding import Binding
from textual.app import ComposeResult
from textual.widgets import DirectoryTree
from textual.containers import Container

from ase.io.formats import ioformats


def build_write_exts() -> set[str]:
    ext_list = []
    for format in ioformats.values():
        # We are only interested in seeing files that we can append to
        # else just write the filename yourself
        if not format.single and format.can_append:
            if format.extensions:
                ext_list.extend(format.extensions)
            else:
                ext_list.append(format.name)
    return set([f'.{ext}' for ext in ext_list])

ASE_IO_WRITE_EXTS = build_write_exts()

def build_read_exts() -> set[str]:
    ext_list = []
    for format in ioformats.values():
        if format.can_read:
            if format.extensions:
                ext_list.extend(format.extensions)
            else:
                ext_list.append(format.name)
    return set([f'.{ext}' for ext in ext_list])

ASE_IO_READ_EXTS = build_read_exts()

class ASEWriteDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths
                if (path.suffix in ASE_IO_WRITE_EXTS or path.is_dir())]
    
class ASEReadDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths
                if (path.suffix in ASE_IO_READ_EXTS or path.is_dir())]


class FilesIOScreen(ModalScreen[Path | None]):
    """Screen with a question that can be answered yes or no."""
    
#     DEFAULT_CSS = """
        # FilesIOScreen {
        #     align: center middle;
        # }

        # YesNoScreen > Label {
        #     text-align: center;
        #     width: 50%;
        #     height: auto;
        #     border: heavy $warning;
        #     padding: 2 4;
        # }
# """
    
    BINDINGS = [
        # ("y", "yes", "Yes"),
        # ("n", "no", "No"),
        # Binding("Y", "yes", "Yes", show=False),
        # Binding("N", "no", "No", show=False),
        Binding("ctrl+g", "cancel", "Cancel", show=False),
    ]

    def __init__(self, read: bool = True) -> None:
        self.read = read
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.read:
            yield Container(Label('Select a file to read from'),
                            ASEReadDirectoryTree(Path(".").resolve()),
                            FolderLabel("Current folder"),
                            Input())
        else:
            yield Container(Label('Select a file to write to'),
                            ASEWriteDirectoryTree(Path(".").resolve()),
                            FolderLabel("Current folder"),
                            Input())
        yield Footer()

    # def action_yes(self) -> None:
    #     self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(None)
        
    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        self.dismiss(Path(submitted.value))
        
    @on(Tree.NodeHighlighted)
    def set_input(self, event: Tree.NodeHighlighted) -> None:
        # Add a / to the end if it is a directory
        path = event.node.data.path
        str_path = str(path)
        if path.is_dir():
            str_path += '/'
        self.query_one(Input).value = str_path

class FolderLabel(Label):
    ...
    

