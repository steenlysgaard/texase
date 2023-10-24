from textual.containers import Container

class ColumnAdd(Container):
    pass

class Search(Container):
    _table = None
    _data = None
    
    def on_input_changed(self, input):
        print("on_input_changed")
        print(input)
        print(self._data.search_for_string(input.value))
        # for row_key, row in self._table.rows.items():
        #     print(row)

