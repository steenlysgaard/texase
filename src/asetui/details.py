from textual.app import ComposeResult
from textual.widgets import Static
from textual.widgets import ListView, ListItem, Label
from textual.containers import Container

list = [ListItem(Label(i)) for i in ['a', 'b', 'c']]

class Details(Container):
    def compose(self) -> ComposeResult:
        yield Title("Key value pairs")
        yield KVPList(*list)
        yield Title("Data")
        yield DataList()
        
    def set_focus(self) -> None:
        # Remember where old focus was and start from this. If this
        # row hasn't been focused before then focus on the KVPList.
        self.query_one(KVPList).focus()
        
    def update_kvplist(self, kvplist: list) -> None:
        self.query_one(KVPList).update(*kvplist)



class Title(Static):
    pass

class KVPList(ListView):
    pass

class DataList(ListView):
    pass
