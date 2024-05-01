from __future__ import annotations

import os
from typing import Any

import typer
from ase.db import connect
from ase.db.core import check
from ase.gui.gui import GUI, Images
from rich.panel import Panel
from textual import on, work
from textual._two_way_dict import TwoWayDict
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.coordinate import Coordinate
from textual.driver import Driver
from textual.reactive import var
from textual.widgets import Footer, Header, Input
from textual.widgets._data_table import ColumnKey, StringKey
from textual.worker import Worker, WorkerState
from typer.rich_utils import (
    ALIGN_ERRORS_PANEL,
    ERRORS_PANEL_TITLE,
    STYLE_ERRORS_PANEL_BORDER,
    _get_rich_console,
)
from typing_extensions import Annotated

from texase.addcolumn import AddColumnBox
from texase.data import ALL_COLUMNS, ASEReadError, ASEWriteError, instantiate_data
from texase.details import Details
from texase.edit import AddBox, EditBox
from texase.files_io import FilesIOScreen
from texase.filter import FilterBox
from texase.formatting import (
    convert_value_to_int_float_or_bool,
    correctly_typed_kvp,
    format_value,
    kvp_exception,
)
from texase.help import HelpScreen
from texase.keys import KeyBox
from texase.search import Search
from texase.table import TexaseTable
from texase.yesno import YesNoScreen


class TEXASE(App):
    BINDINGS = [
        Binding("ctrl+g", "hide_all", "Hide all boxes", show=False),
        Binding("ctrl+z", "suspend_process", "Suspend the app", show=False),
    ]

    CSS_PATH = "texase.tcss"

    # variables that are watched. Remember also to add them to the
    # action_hide_all function
    show_details = var(False)
    show_add_column_box = var(False)
    show_search_box = var(False)
    show_filter = var(False)
    show_edit = var(False)
    show_add_kvp = var(False)

    def __init__(self, path: str) -> None:
        self.path = path
        self.sort_columns: list[str] = ["id"]
        self.sort_reverse: bool = False
        self.gui: GUI | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield Footer()
        yield MiddleContainer(
            # Boxes put centered at the top, but in a higher layer, of the table
            FilterBox(id="filter-box", classes="topbox"),
            # Boxes docked at the bottom in the same layer of the table
            Search(
                Input(id="search-input", placeholder="Search.."),
                classes="bottombox",
                id="search-box",
            ),
            EditBox(id="edit-box", classes="bottombox"),
            AddBox(id="add-kvp-box", classes="bottombox"),
            AddColumnBox(id="add-column-box", classes="bottombox"),
            # Other boxes
            Details(id="details"),
            TexaseTable(id="table"),
            KeyBox(id="key-box"),
        )

    async def on_mount(self) -> None:
        # Table
        table = self.query_one(TexaseTable)

        self.load_initial_data(table)

        table.focus()

        self.finish_mounting()

    @work
    async def finish_mounting(self) -> None:
        # Load the rest of the data
        table = self.query_one(TexaseTable)

        key_box = self.query_one(KeyBox)
        key_box.loading = True

        self.load_remaining_data(table)

    async def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """If load remaining data is done, stop loading, notify and populate key box."""
        if (
            event.worker.name == "load_remaining_data"
            and event.worker.state == WorkerState.SUCCESS
        ):
            key_box = self.query_one(KeyBox)
            key_box.loading = False

            # TODO: check that additional keys are added after initial load
            await self.populate_key_box()  # type: ignore

            self.notify("Loading Done!", severity="information", timeout=1.5)

    def load_initial_data(self, table: TexaseTable) -> None:
        # db data
        data = instantiate_data(self.path, limit=100)
        self.data = data

        table.populate_table(data)

    @work(thread=True)
    def load_remaining_data(self, table: TexaseTable) -> None:
        indices = self.data.add_remaining_rows_to_df()
        if len(indices) > 0:
            self.call_from_thread(table.add_table_rows, self.data, indices)

    async def populate_key_box(self) -> None:
        key_box = self.query_one(KeyBox)
        await key_box.populate_keys(self.data.unused_columns())

    def remove_filter_from_table(self, filter_tuple: tuple) -> None:
        self.query_one(TexaseTable).remove_filter(*filter_tuple)

    # Import / Export

    @work
    async def action_export_rows(self) -> None:
        """Export the marked rows or selected row of the table to a file"""
        table = self.query_one(TexaseTable)
        ids = table.ids_to_act_on()

        # Show the directory tree with an input box to select a file
        # name and location
        output_file = await self.push_screen_wait(FilesIOScreen(False))
        if output_file is not None:
            try:
                self.data.export_rows(ids, output_file)
            except ASEWriteError as e:
                self.notify_error(
                    f"ASE cannot write to the file {output_file}, it gives:\n {e}",
                    "ASE write error",
                    timeout=5,
                )

    @work
    async def action_import_rows(self) -> None:
        """Export the marked rows or selected row of the table to a file"""
        input_file = await self.push_screen_wait(FilesIOScreen(True))
        if input_file is not None:
            # Put info in db and data.df
            try:
                added_indices = self.data.import_rows(input_file)
            except ASEReadError as e:
                self.notify_error(
                    f"ASE cannot read the file {input_file}, it gives:\n {e}",
                    "ASE read error",
                    timeout=5,
                )
            else:
                # Clear and reoccupy the table
                table = self.query_one(TexaseTable)
                table.loading = True
                table.add_table_rows(self.data, indices=added_indices)

                # Update KeyBox
                await self.populate_key_box()

                table.loading = False
                table.focus()

    # Sorting
    def action_sort_column(self) -> None:
        # Get the highlighted column
        table = self.query_one(TexaseTable)
        self.sort_table(table.column_at_cursor(), table)

    def on_data_table_header_selected(
        self, selected: TexaseTable.HeaderSelected
    ) -> None:
        table = selected.data_table
        col_name = str(selected.label)
        self.sort_table(col_name, table)

    def sort_table(self, col_name: str, table: TexaseTable) -> None:
        # Save the row key of the current cursor position
        row_key = table.coordinate_to_cell_key(Coordinate(table.cursor_row, 0)).row_key

        # Sort the table
        ordered_index = self.data.sort(col_name)

        table._row_locations = TwoWayDict(
            {
                StringKey(str(key)): new_index
                for new_index, key in enumerate(ordered_index)
            }
        )
        table._update_count += 1
        table.refresh()

        # After finished sort make the cursor go to the same cell as before sorting
        table.cursor_coordinate = Coordinate(
            table._row_locations.get(row_key), table.cursor_column
        )

        # How sort does it:
        # self._row_locations = TwoWayDict(
        #     {key: new_index for new_index, (key, _) in enumerate(ordered_rows)}
        # )
        # self._update_count += 1
        # self.refresh()
        # table.sort(*self.sort_columns, reverse=self.sort_reverse)

    # Details sidebar
    def action_toggle_details(self) -> None:
        self.show_details = not self.show_details
        table = self.query_one(TexaseTable)
        if self.show_details:
            # Get the highlighted row
            row_id = table.row_id_at_cursor()
            details = self.query_one(Details)
            details.clear_modified_and_deleted_keys()
            details.update_kvplist(*self.data.row_details(row_id))
            details.update_data(self.data.row_data(row_id))

            # Set focus on the details sidebar
            details.set_focus()

        else:
            # Set focus back on the table
            table.focus()

    def save_details(
        self, key_value_pairs: dict, data: dict, deleted_keys: set
    ) -> None:
        """Called when the user calls save in the details sidebar."""

        # Add deleted keys to key_value_pairs with None values
        for key in deleted_keys:
            key_value_pairs[key] = None

        table = self.query_one(TexaseTable)
        table.update_row_editable_cells(key_value_pairs)

        row_id = table.row_id_at_cursor()
        self.data.update_row(row_id, key_value_pairs, data)

    def watch_show_details(self, show_details: bool) -> None:
        """Called when show_details is modified."""
        dv = self.query_one(Details)
        dv.display = show_details

    def action_hide_all(self) -> None:
        self.show_details = False
        self.show_add_column_box = False
        self.show_search_box = False
        self.show_filter = False
        self.show_edit = False
        self.show_add_kvp = False
        self.query_one(TexaseTable).focus()

    # Help screen
    def action_toggle_help(self) -> None:
        self.push_screen(HelpScreen())

    # Add/Delete key-value-pairs
    def action_add_key_value_pair(self) -> None:
        table = self.query_one(TexaseTable)
        self.show_add_kvp = True
        addbox = self.query_one("#add-kvp-box", AddBox)
        table.update_add_box(addbox)
        addbox.focus()

    def watch_show_add_kvp(self, show_add_kvp: bool) -> None:
        box = self.query_one("#add-kvp-box")
        box.display = show_add_kvp

    @work
    async def action_delete_key_value_pairs(self) -> None:
        table = self.query_one(TexaseTable)
        if not table.is_cell_editable(uneditable_columns=ALL_COLUMNS):
            return
        question = table.delete_kvp_question()
        if await self.push_screen_wait(YesNoScreen(question)):
            table.delete_selected_key_value_pairs()

            # Remove in db and df
            column_name = table.column_at_cursor()
            self.data.update_value(
                table.ids_to_act_on(), column=column_name, value=None
            )

        # If no other key value pairs are present in the column, delete the column from the table
        self.data.clean_user_keys()
        table.check_columns(self.data)

    # Delete rows
    @work
    async def action_delete_rows(self) -> None:
        """Delete the currently marked rows."""
        table = self.query_one(TexaseTable)
        if await self.push_screen_wait(YesNoScreen(table.delete_row_question())):
            # Remove in db and df
            self.data.delete_rows_from_df_and_db(table.ids_to_act_on())

            # Then remove in table
            table.delete_selected_rows()

    # Edit
    def action_edit(self) -> None:
        table = self.query_one(TexaseTable)
        if table.is_cell_editable():
            self.show_edit = True
            editbox = self.query_one("#edit-box", EditBox)
            table.update_edit_box(editbox)
            editbox.focus()

    def watch_show_edit(self, show_edit: bool) -> None:
        editbox = self.query_one("#edit-box")
        editbox.display = show_edit

    # Search
    def action_search(self) -> None:
        # show_search_box is set to True since the search bar is able
        # to close itself after a search.
        self.show_search_box = True
        search_input = self.query_one("#search-input")
        search_input.focus()  # This is the input box

        search = self.query_one(Search)
        search._table = self.query_one(TexaseTable)
        search._data = self.data
        search_input.value = ""
        search.set_current_cursor_coordinate()

    def watch_show_search_box(self, show_search_box: bool) -> None:
        searchbar = self.query_one(Search)
        searchbar.display = show_search_box

    # Filter
    async def action_filter(self) -> None:
        self.show_filter = True
        filterbox = self.query_one("#filter-box", FilterBox)
        await filterbox.focus_filterbox()

    def watch_show_filter(self, show_filter: bool) -> None:
        searchbar = self.query_one("#filter-box")
        searchbar.display = show_filter

    # Column action
    def action_add_column(self) -> None:
        self.show_add_column_box = True
        self.query_one("#add-column-box").focus()

    def watch_show_add_column_box(self, show_box: bool) -> None:
        addcolumnbox = self.query_one(AddColumnBox)
        addcolumnbox.display = show_box

    async def action_remove_column(self) -> None:
        """Remove the column that the cursor is on.

        Also remove the column from chosen_columns."""

        table = self.query_one(TexaseTable)
        # Save the name of the column to remove
        cursor_column_index = table.cursor_column
        column_to_remove = str(table.ordered_columns[cursor_column_index].label)

        # Add the column to the KeyBox
        await self.query_one(KeyBox).add_key(column_to_remove)

        self.remove_column_from_table(column_to_remove)

    def remove_column_from_table(self, column_name: str) -> None:
        table = self.query_one(TexaseTable)
        # Remove the column from the table in data
        self.data.remove_from_chosen_columns(column_name)

        # col_key = table.ordered_columns[cursor_column_index].key
        col_key = ColumnKey(column_name)
        table.remove_column(col_key)

    def action_view(self) -> None:
        """View the currently selected images, if no images are
        selected then view the row the cursor is on"""
        table = self.query_one(TexaseTable)
        if table.marked_rows:
            images = [self.data.get_atoms(id) for id in table.get_marked_row_ids()]
        else:
            images = [self.data.get_atoms(table.row_id_at_cursor())]
        self.gui = GUI(Images(images))
        # Only run if we are not doing a pytest
        if "PYTEST_CURRENT_TEST" not in os.environ:
            self.gui.run()

    def add_column_to_table_and_remove_from_keybox(self, column: str) -> None:
        """Add a column to the table and remove it from the KeyBox."""
        table = self.query_one(TexaseTable)
        self.data.add_to_chosen_columns(column)
        table.add_column_and_values(column)
        self.query_one(KeyBox).remove_key(column)

    def on_input_submitted(self, submitted: Input.Submitted):
        table = self.query_one(TexaseTable)
        if (
            submitted.validation_result is not None
            and not submitted.validation_result.is_valid
        ):
            return
        if submitted.control.id == "add-column-input":
            self.add_column_to_table_and_remove_from_keybox(submitted.value)

            self.show_add_column_box = False
            table.focus()
        elif submitted.control.id == "edit-input":
            column = table.column_at_cursor()
            if column == "pbc":
                value = submitted.value.upper()
            else:
                value = convert_value_to_int_float_or_bool(submitted.value)

            exception_from_kvp = kvp_exception(column, value)
            if exception_from_kvp is not None:
                self.notify_error(exception_from_kvp, "ValueError")
                return

            # kvp is ok, but give a warning if type changed
            self.notify_if_kvp_type_changed(
                column, value, table.get_cell_at(table.cursor_coordinate)
            )

            # Update table
            table.update_cell_from_edit_box(format_value(value))

            # Update data
            self.data.update_value(
                ids=table.row_id_at_cursor(),
                column=table.column_at_cursor(),
                value=value,
            )

            # Go back to original view
            self.show_edit = False
            table.focus()

        elif submitted.control.id == "add-input":
            key, value = correctly_typed_kvp(submitted.value)

            exception_from_kvp = kvp_exception(key, value)
            if exception_from_kvp is not None:
                self.notify_error(exception_from_kvp, "ValueError")
                return

            # Add to chosen_columns and user_keys in data
            self.data.add_new_user_key(key, show=True)

            # Update data
            if table.marked_rows:
                # If there are marked rows, add the key value pair to
                # all marked rows
                self.data.update_value(
                    ids=table.get_marked_row_ids(), column=key, value=value
                )
            else:
                # If there are no marked rows, add the key value pair
                # to the row the cursor is on
                self.data.update_value(
                    ids=table.row_id_at_cursor(), column=key, value=value
                )

            # Update table
            table.update_cell_from_add_box(key, format_value(value))

            # Go back to original view
            self.show_add_kvp = False
            table.focus()

    def notify_if_kvp_type_changed(
        self, key: str, new_value: Any, old_value: Any
    ) -> None:
        if not isinstance(new_value, type(old_value)):
            self.notify(
                f"The type of [bold]{key} = {new_value}[/bold] has changed from "
                + f"[bold]{type(old_value).__name__}[/bold] to [bold]{type(new_value).__name__}[/bold].",
                severity="warning",
            )

    # Shouldn't this be deleted??
    def is_kvp_valid(self, key, value):
        """Check that key-value-pair is valid for ase.db

        It is ok to edit pbc, we make this check first."""

        if key == "pbc":
            try:
                check_pbc_string_validity(value)
            except ValueError as e:
                self.notify_error(str(e), "ValueError")
                return False
            return True

        try:
            check({key: value})
        except ValueError as e:
            # Notify that the key-value-pair is not valid with the
            # raised ValueError and then return
            self.notify_error(str(e), "ValueError")
            return False
        return True

    def notify_error(self, e: str, error_title: str, timeout: float = 3) -> None:
        self.notify(
            e,
            severity="error",
            title=error_title,
            timeout=timeout,
        )

    def action_quit(self) -> None:
        self.data.save_chosen_columns()
        super().exit()

    def action_suspend_process(self) -> None:
        self.data.save_chosen_columns()
        super().action_suspend_process()

    @on(Driver.SignalResume)
    @work
    async def action_update_view(self) -> None:
        """Check if the db has been updated since it was last read.

        If so update the table."""
        # if not self.data.is_df_up_to_date():
        remove_idx, update_idx, add_idx = self.data.updates_from_db()

        table = self.query_one(TexaseTable)
        table.delete_rows([table.row_index_to_row_key(idx) for idx in remove_idx])

        table.add_table_rows(self.data, add_idx)
        table.update_table_rows(self.data, update_idx)

        table.check_columns(self.data)

        # Update the KeyBox
        await self.populate_key_box()


def check_pbc_string_validity(string):
    """Check if the string is a valid pbc string. I.e. on the form TTT, TFT, FFF, etc."""
    # check if the string has exactly three characters
    if len(string) == 3:
        # convert the string to upper case
        string = string.upper()
        # loop through each character in the string
        for char in string:
            # check if the character is either t or f
            if char not in ["T", "F"]:
                # raise a ValueError with a descriptive message
                raise ValueError(f"{string} contains characters that are not T or F!")
        # return True if all characters are t or f
        return True
    else:
        # raise a ValueError with a descriptive message
        raise ValueError(f"{string} does not have exactly three characters!")


def is_db_empty(db_path: str) -> bool:
    """Check if the database is empty."""
    # Quick test of a db file. If it doesn't exist, it's empty.
    if not os.path.exists(db_path):
        return True
    return len(connect(db_path)) == 0


class MiddleContainer(Container):
    pass


typer_app = typer.Typer()


@typer_app.command()
def main(db_path: Annotated[str, typer.Argument(help="Path to the ASE database")]):
    if is_db_empty(db_path):
        error = Panel(
            f"The database [bold]{db_path}[/bold] is empty!",
            border_style=STYLE_ERRORS_PANEL_BORDER,
            title=ERRORS_PANEL_TITLE,
            title_align=ALIGN_ERRORS_PANEL,
        )
        console = _get_rich_console(stderr=True)
        console.print(error)
        raise typer.Exit(code=1)
    app = TEXASE(path=db_path)
    app.run()


if __name__ == "__main__":
    typer_app()
