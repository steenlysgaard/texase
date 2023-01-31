from textual.app import ComposeResult
from textual.widgets import Static
from textual.widgets import ListView
from textual.containers import Container
from rich.text import Text


class Details(Container):
    def compose(self) -> ComposeResult:
        yield Title("Key value pairs")
        yield Container(KVPStatic(), KVPList())
        yield Title("Data")
        yield DataList()

    def set_focus(self) -> None:
        # Remember where old focus was and start from this. If this
        # row hasn't been focused before then focus on the KVPList.
        self.query_one(KVPList).focus()

    def update_kvplist(self, static_kvps: Text, dynamic_kvps: list) -> None:
        """Update the kvp widgets."""
        # Static (non-editable) key value pairs
        self.query_one(KVPStatic).update(static_kvps)

        # Dynamic (editable) key value pairs
        kvp_widget = self.query_one(KVPList)
        kvp_widget.clear()
        for kvp in dynamic_kvps:
            kvp_widget.append(kvp)


class Title(Static):
    pass


class KVPStatic(Static):
    pass


class KVPList(ListView):
    pass


class DataList(ListView):
    pass
