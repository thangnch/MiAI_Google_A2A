import mesop as me

from components.header import header
from components.page_scaffold import page_scaffold
from components.page_scaffold import page_frame
from state.state import SettingsState


def on_selection_change_output_types(e: me.SelectSelectionChangeEvent):
  s = me.state(SettingsState)
  s.output_mime_types = e.values


def settings_page_content():
    """Settings Page Content."""
    settings_state = me.state(SettingsState)
    with page_scaffold():  # pylint: disable=not-context-manager
        with page_frame():
            with header("Settings", "settings"): pass
            with me.box(
                style=me.Style(
                    display="flex",
                    justify_content="space-between",
                    flex_direction="column",
                )
            ):
                me.select(
                    label="Supported Output Types",
                    options=[
                        me.SelectOption(label="Image", value="image/*"),
                        me.SelectOption(label="Text (Plain)", value="text/plain"),
                    ],
                    on_selection_change=on_selection_change_output_types,
                    style=me.Style(width=500),
                    multiple=True,
                    appearance="outline",
                    value=settings_state.output_mime_types,
                )


