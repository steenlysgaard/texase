from __future__ import annotations

from textual.app import ComposeResult
from textual import on
from textual.widgets import Label, Input
from textual.widgets import ListView, ListItem
from textual.containers import Container, Horizontal
from rich.text import Text

from asetui.formatting import convert_value_to_int_or_float, get_age_string


class Details(Container):
    BINDINGS = [
        # Hiding boxes shortcut is already defined in app, just
        # redefining the binding here to make it show in the edit
        # box
        ("ctrl+g", "hide_edit", "Undo/Hide"),
        ("ctrl+s", "save", "Save changes"),
        ("ctrl+d", "delete", "Delete"),
    ]
    
    modified_keys: set = set()
    deleted_keys: set = set()
    
    def compose(self) -> ComposeResult:
        yield Title(
            "Key value pairs ([@click=\"app.open_link('https://wiki.fysik.dtu.dk/ase/ase/units.html')\"]Units[/])"
        )
        yield Container(KVPStatic(), KVPList(), id="kvp")
        yield Title("Data")
        yield DataList(id="datalist")

    def set_focus(self) -> None:
        # Remember where old focus was and start from this. If this
        # row hasn't been focused before then focus on the KVPList.
        self.query_one(KVPList).focus()

    def update_kvplist(self, static_kvps: dict, dynamic_kvps: dict) -> None:
        """Update the kvp widgets."""
        # Static (non-editable) key value pairs
        static_str = ""
        for key, value in static_kvps.items():
            if key == 'age':
                value = get_age_string(value)
            static_str += f"[bold]{key}: [/bold]{value}\n"
        self.query_one(KVPStatic).update(Text.from_markup(static_str))

        # Dynamic (editable) key value pairs
        kvp_widget = self.query_one(KVPList)
        kvp_widget.clear()
        for key, value in dynamic_kvps.items():
            kvp_widget.append(ListItem(EditableItem(key, value)))
            
    def update_data(self, dynamic_data: list) -> None:
        data_widget = self.query_one(DataList)
        data_widget.clear()
        for kvp in dynamic_data:
            data_widget.append(kvp)

    def on_hide(self) -> None:
        self.clear_modified_and_deleted_keys()

    def clear_modified_and_deleted_keys(self) -> None:
        self.modified_keys = set()
        self.deleted_keys = set()
            
    def on_list_view_selected(self, sender):
        """When a row is selected in the KVPList, focus on the input
        field and remember that this key value pair was potentially
        modifed."""
        item = sender.item.get_child_by_type(EditableItem)
        item.focus()
        self.modified_keys.add(item.key)
        
    def action_save(self) -> None:
        """Save the changes to the table, dataframe and database."""

        # Get the key value pairs from the KVPList
        key_value_pairs = {}
        for h in self.query_one(KVPList).children:
            item = h.get_child_by_type(EditableItem)
            key = item.key
            if key in self.modified_keys:
                key_value_pairs[key] = item.value
        self.app.save_details(key_value_pairs, None, self.deleted_keys)
        self.clear_modified_and_deleted_keys()
        
    def action_delete(self) -> None:
        """Delete the current key value pair or data."""
        kvplist = self.query_one(KVPList)
        selected_key = kvplist.selected_key()
        if selected_key is not None:
            self.deleted_keys.add(selected_key)
        kvplist.delete_selected()

class EditableItem(Horizontal):
    def __init__(self, key, value):
        super().__init__()
        self.key = key
        self.value = value
    
    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self.key} = [/bold]")
        yield Input(value=f"{self.value}", classes="editable-input")
        
    def focus(self) -> None:
        self.query_one(Input).focus()
        
    def on_input_submitted(self, submitted: Input.Submitted):
        """When the user presses enter in the input field, update the value.

        Then the KVPList takes back focus.
        """
        # TODO: Exactly the same code as in app.py. Refactor?
        if self.key == 'pbc':
            value = submitted.value.upper()
        else:
            value = convert_value_to_int_or_float(submitted.value)
        if not self.app.is_kvp_valid(self.key, value):
            submitted.stop()  # stop bubbling further
            return
        
        self.value = value
        
        
class Title(Label):
    pass


class KVPStatic(Label):
    pass


class KVPList(ListView):
    @on(Input.Submitted)
    def take_back_focus(self, _):
        """When the user presses enter in the input field, take back focus."""
        self.focus()
        
    def delete_selected(self) -> None:
        """Delete the current key value pair."""
        current_index = self.index
        if self.highlighted_child is not None:
            self.highlighted_child.remove()
        self.index = current_index
        
    def selected_key(self) -> str | None:
        """Return the key of the currently selected key value pair."""
        if self.highlighted_child is not None:
            return self.highlighted_child.get_child_by_type(EditableItem).key


class DataList(ListView):
    pass
