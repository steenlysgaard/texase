from __future__ import annotations

from textual.app import ComposeResult
from textual import on, work
from textual.widgets import Label, Input
from textual.widgets import ListView, ListItem
from textual.message import Message
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from rich.text import Text

from texase.formatting import (
    convert_str_to_other_type,
    convert_value_to_int_float_or_bool,
    get_age_string,
)
from texase.validators import kvp_validators_edit
from texase.input_screens import KVPScreen, DataScreen


class Details(Container):
    BINDINGS = [
        # Hiding boxes shortcut is already defined in app, just
        # redefining the binding here to make it show in the edit
        # box
        ("ctrl+g", "hide_edit", "Undo/Hide"),
        ("ctrl+s", "save", "Save changes"),
        ("ctrl+d", "delete", "Delete"),
        ("k", "add_kvp", "Add key value pair"),
        ("d", "add_data", "Add data"),
    ]

    modified_keys = set()
    deleted_keys = set()
    # Watch if anything is modified. If so, show a label that says unsaved changes.
    anything_modified = reactive(False)

    def compose(self) -> ComposeResult:
        yield Title(
            "Key value pairs ([@click=\"app.open_link('https://wiki.fysik.dtu.dk/ase/ase/units.html')\"]Units[/])"
        )
        yield Container(KVPStatic(), KVPList(id="dynamic_kvp_list"), id="kvp")
        yield Title("Data")
        yield DataList(id="datalist")
        yield Label("Unsaved changes!", id="unsaved_changes")

    def watch_anything_modified(self, modified):
        if modified:
            self.query_one("#unsaved_changes", Label).remove_class("-hidden")
        else:
            self.query_one("#unsaved_changes", Label).add_class("-hidden")

    def set_focus(self) -> None:
        # Remember where old focus was and start from this. If this
        # row hasn't been focused before then focus on the KVPList.
        self.query_one("#dynamic_kvp_list", KVPList).focus()

    def update_kvplist(self, static_kvps: dict, dynamic_kvps: dict) -> None:
        """Update the kvp widgets."""
        # Static (non-editable) key value pairs
        static_str = ""
        for key, value in static_kvps.items():
            if key == "age":
                value = get_age_string(value)
            static_str += f"[bold]{key}: [/bold]{value}\n"
        self.query_one(KVPStatic).update(Text.from_markup(static_str))

        # Dynamic (editable) key value pairs
        kvp_widget = self.query_one("#dynamic_kvp_list", KVPList)
        kvp_widget.clear()
        for key, value in dynamic_kvps.items():
            kvp_widget.append(ListItem(EditableItem(key, value)))

    def update_data(self, dynamic_data: dict) -> None:
        data_widget = self.query_one(DataList)
        data_widget.clear()
        for key, value in dynamic_data.items():
            data_widget.append(ListItem(DataItem(key, value)))

    def on_hide(self) -> None:
        self.clear_modified_and_deleted_keys()

    def clear_modified_and_deleted_keys(self) -> None:
        self.modified_keys.clear()
        self.deleted_keys.clear()
        self.anything_modified = False

    def on_details_list_item_selected(self, sender: DetailsList.ItemSelected):
        self.add_key_to_modified(sender.item.key)
        
    def add_key_to_modified(self, key: str) -> None:
        self.modified_keys.add(key)
        self.anything_modified = True

    def action_save(self) -> None:
        """Save the changes to the table, dataframe and database."""

        # Get the key value pairs from the KVPList
        key_value_pairs = {}
        for h in self.query_one("#dynamic_kvp_list", KVPList).children:
            item = h.get_child_by_type(EditableItem)
            key = item.key
            if key in self.modified_keys:
                key_value_pairs[key] = item.value

        # Do the same for updated data
        updated_data = {}
        for h in self.query_one("#datalist", DataList).children:
            item = h.get_child_by_type(DataItem)
            key = item.key
            if key in self.modified_keys:
                updated_data[key] = item.value

        self.app.save_details(key_value_pairs, updated_data, self.deleted_keys)
        self.clear_modified_and_deleted_keys()

    def action_delete(self) -> None:
        """Delete the current key value pair. If the selection is on
        the DataList then notify that ASE can't delete data items in a
        row."""
        focused_list: DetailsList = self.app.focused
        if isinstance(focused_list, DataList):
            self.notify("ASE can't delete data items in a row.", severity="information")
            return
        selected_key = focused_list.selected_key()
        if selected_key is not None:
            self.deleted_keys.add(selected_key)
            self.anything_modified = True
        focused_list.delete_selected()

    @work
    async def action_add_data(self) -> None:
        """Add a new data item."""
        new_data = await self.app.push_screen_wait(DataScreen("Add data"))
        if new_data is not None:
            key, value = new_data
            self.query_one(DataList).append(ListItem(DataItem(key, value)))
            self.add_key_to_modified(key)

    @work
    async def action_add_kvp(self) -> None:
        """Add a new key value pair item."""
        new_kvp = await self.app.push_screen_wait(KVPScreen("Add key value pair"))
        if new_kvp is not None:
            key, value = new_kvp
            self.query_one(KVPList).append(ListItem(EditableItem(key, value)))
            self.add_key_to_modified(key)


class Item(Horizontal):
    validators = []

    def __init__(self, key, value):
        super().__init__()
        self.key = key
        # TODO: Check if value changes type when editing, if so ask if it's ok.
        self.value = value

    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self.key} = [/bold]")
        yield Input(
            value=f"{self.value}",
            classes="editable-input",
            validators=self.validators,
            validate_on=["submitted"],
        )

    def focus(self) -> None:
        self.query_one(Input).focus()


class EditableItem(Item):
    validators = kvp_validators_edit

    def on_input_submitted(self, submitted: Input.Submitted):
        """When the user presses enter in the input field, update the value.

        Then the KVPList takes back focus.
        """
        # TODO: Exactly the same code as in app.py. Refactor?
        if submitted.validation_result is not None and not submitted.validation_result.is_valid:
            self.app.notify_error("\n".join(submitted.validation_result.failure_descriptions),
                                  error_title="Invalid input",)
            # If not valid input stop bubbling further
            submitted.stop()
            return

        if self.key == "pbc":
            value = submitted.value.upper()
        else:
            value = convert_value_to_int_float_or_bool(submitted.value)

        if not self.app.is_kvp_valid(self.key, value):
            submitted.stop()  # stop bubbling further
            return

        self.value = value


class DataItem(Item):
    def on_input_submitted(self, submitted: Input.Submitted):
        """When the user presses enter in the input field, update the value.

        Then the DataList takes back focus.
        """
        if submitted.validation_result is not None and not submitted.validation_result.is_valid:
            self.app.notify_error("\n".join(submitted.validation_result.failure_descriptions),
                                  error_title="Invalid input",)
            # If not valid input stop bubbling further
            submitted.stop()
            return

        value = convert_str_to_other_type(submitted.value)
        self.value = value


class Title(Label):
    pass


class KVPStatic(Label):
    pass


class DetailsList(ListView):
    class ItemSelected(Message):
        """Color selected message."""

        def __init__(self, item: Item) -> None:
            self.item = item
            super().__init__()

    def on_list_view_selected(self, sender):
        """When a row is selected in the KVPList, focus on the input
        field and remember that this key value pair was potentially
        modifed."""
        item = sender.item.children[0]
        item.focus()
        self.post_message(self.ItemSelected(item))

    @on(Input.Submitted)
    def take_back_focus(self, submitted: Input.Submitted):
        """When the user presses enter in the input field, take back
        focus. It is assumed that the input value is valid."""
        self.focus()

    def delete_selected(self) -> None:
        """Delete the current key value pair."""
        current_index = self.index
        if self.highlighted_child is not None:
            self.highlighted_child.remove()
        self.index = current_index

    def selected_key(self) -> str | None:
        raise NotImplementedError("selected_key must be implemented in subclass.")


class KVPList(DetailsList):
    def selected_key(self) -> str | None:
        """Return the key of the currently selected key value pair."""
        if self.highlighted_child is not None:
            return self.highlighted_child.get_child_by_type(EditableItem).key

class DataList(DetailsList):
    def selected_key(self) -> str | None:
        """Return the key of the currently selected key value pair."""
        if self.highlighted_child is not None:
            return self.highlighted_child.get_child_by_type(DataItem).key
        
    def delete_selected(self) -> None:
        raise NotImplementedError("ASE can't delete data items in a row.")
