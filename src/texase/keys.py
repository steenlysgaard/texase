from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.widgets import Button, Label


class KeyBox(Horizontal):
    async def add_key(self, key: str) -> None:
        new_key = Key(key, id=f"key-{key}")
        await self.mount(new_key)

    def remove_key(self, key: str) -> None:
        key_button = self.query_one(f"#key-{key}", Key)
        key_button.remove()

    def compose(self) -> ComposeResult:
        yield Label("Other keys:")

    async def populate_keys(self, keys: list[str]) -> None:
        """Populate KeyBox with the given keys.

        Also remove superfluous keys."""
        for key_node in self.query(Key).nodes:
            key_name = str(key_node.id).replace("key-", "")
            if key_name not in keys:
                key_node.remove()
                # self.remove_key(key_name)
        for key in keys:
            # Only add the key if it doesn't already exist
            try:
                self.query_one(f"#key-{key}", Key)
            except NoMatches:
                await self.add_key(key)

    @on(Button.Pressed)
    def add_column_to_table(self, event: Button.Pressed) -> None:
        self.app.add_column_to_table_and_remove_from_keybox(str(event.button.label))


class Key(Button):
    DEFAULT_CSS = """
    Key {
        border: none;
        height: 1;
        min-width: 3;
        padding: 0;
        padding-right: 0;
        padding-left: 0;
    }
    """
