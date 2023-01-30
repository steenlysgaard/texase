from textual.widgets import Static
from textual.widgets import Placeholder
from textual.widgets import DataTable
from textual.containers import Horizontal, Vertical

class DV(Placeholder):
    BINDINGS = [("escape", "hide", "Hide")]
    # display = True

    # def __init__(self, *args, **kwargs):
    #     # self.display = False
    #     super().__init__(*args, **kwargs)

    def make_visible(self, cell):
        self.display = True
        print(cell)
        
    def action_hide(self):
        self.display = False
        
# class Details(Static):
#     # BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

#     def __init__(self, *args, **kwargs) -> None:
#         self.visibility = False
#         super().__init__(*args, **kwargs)
        
#     def make_visible(self, cell):
#         print(cell)
        
#     def on_mount(self) -> None:
#         # self.update(f'{self.cell}')
#         self.update('heeheheh')

# class DetailsTable(DataTable):
    
