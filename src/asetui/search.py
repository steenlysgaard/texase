from textual.containers import Container

class ColumnAdd(Container):
    pass

class Search(Container):
    _table = None
    
    def on_input_changed(self, input):
        print(input)
        for row_key, row in self._table.rows.items():
            print(row)

