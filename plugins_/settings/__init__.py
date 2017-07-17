# -*- encoding: utf-8 -*-
import logging
import os

import sublime
import sublime_plugin

from ..lib import get_setting
from ..lib.sublime_lib.constants import style_flags_from_list

from .region_math import VALUE_SCOPE, KEY_SCOPE, get_key_region_at, get_last_key_region
from .known_settings import KnownSettings

__all__ = (
    'SettingsListener',
    'GlobalSettingsListener',
)

POPUP_TEMPLATE = """
<body id="sublime-settings">
<style>
    body {{
        margin: 0;
        padding: 0;
    }}
    h1, h2 {{
        border-bottom: 1px solid color(var(--background) blend(white 80%));
        font-weight: normal;
        margin: 0;
        padding: 0.5rem 0.6rem;
    }}
    h1 {{
        color: color(var(--background) blend(var(--orangish) 20%));
        font-size: 1.0rem;
    }}
    h2 {{
        color: color(var(--background) blend(var(--foreground) 30%));
        font-size: 1.0rem;
        font-family: monospace;
    }}
    p {{
        margin: 0;
        padding: 0.5rem;
    }}
    a {{
        text-decoration: none;
    }}
</style>
{0}
</body>
"""

# user package pattern
USER_PATH = "{0}Packages{0}User{0}".format(os.sep)

# logging
l = logging.getLogger(__name__)


class SettingsListener(sublime_plugin.ViewEventListener):

    is_completing_key = False

    @classmethod
    def is_applicable(cls, settings):
        """Enable the listener for Sublime Settings syntax only."""
        syntax = settings.get('syntax') or ""
        return syntax.endswith("/Sublime Text Settings.sublime-syntax")

    def __init__(self, view):
        """Initialize view event listener object."""
        # Need this "hack" to allow reloading of the module,
        # because `super` tries to use the old reference (I think?).
        # See also https://lists.gt.net/python/python/139992
        sublime_plugin.ViewEventListener.__init__(self, view)

        filepath = view.file_name()
        l.debug("initializing SettingsListener for %r", view.file_name())
        if filepath and filepath.endswith(".sublime-settings"):
            filename = os.path.basename(filepath)
            self.known_settings = KnownSettings(filename)
            self.known_settings.add_on_loaded(self.do_linting)
        else:
            self.known_settings = None
            l.error("Not a Sublime Text Settings file: %r", filepath)

    def __del__(self):
        l.debug("deleting SettingsListener instance for %r", self.view.file_name())
        self.view.erase_regions('unknown_settings_keys')

    def on_modified_async(self):
        """Sublime Text modified event handler to update linting."""
        self.do_linting()

    def on_query_completions(self, prefix, locations):
        """Sublime Text query completions event handler.

        Create a list with completions for all known settings or values.

        Arguments:
            prefix (string):
                the line content before cursor
            locations (list of int):
                the text positions of all characters in prefix

        Returns:
            tuple ([ [trigger, content], [trigger, content] ], flags):
                the tuple with content ST needs to display completions
        """
        if self.known_settings and len(locations) == 1:
            point = locations[0]
            if self.view.match_selector(point, VALUE_SCOPE):
                self.is_completing_key = False
                completions_aggregator = self.known_settings.value_completions
            else:
                completions_aggregator = self.known_settings.key_completions
                self.is_completing_key = True
            return completions_aggregator(self.view, prefix, point)

    def on_hover(self, point, hover_zone):
        """Sublime Text hover event handler to show tooltip if needed."""
        # not a settings file or not hovering text
        if not self.known_settings or hover_zone != sublime.HOVER_TEXT:
            return
        # settings key name under cursor
        key_region = get_key_region_at(self.view, point)
        if not key_region:
            return

        self.show_popup_for(key_region)

    def show_popup_for(self, key_region):
        key = self.view.substr(key_region)

        body = self.known_settings.build_tooltip(self.view, key)
        window_width = min(1000, int(self.view.viewport_extent()[0]) - 64)
        # offset <h1> padding, if possible
        key_start = key_region.begin()
        location = max(key_start - 1, self.view.line(key_start).begin())

        self.view.show_popup(
            content=POPUP_TEMPLATE.format(body),
            on_navigate=self.on_navigate,
            location=location,
            max_width=window_width,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY | sublime.COOPERATE_WITH_AUTO_COMPLETE
        )

    def on_navigate(self, href):
        """Popup navigation event handler."""
        command, argument = href.split(":")
        if command == 'edit':
            view_id = self.view.settings().get('edit_settings_other_view_id')
            user_view = sublime.View(view_id)
            if not user_view.is_valid():
                return
            result = user_view.find('"{}"'.format(argument), 0)
            self.view.hide_popup()
            if self.view.window():
                self.view.window().focus_view(user_view)
            if result.a == -1:
                self.known_settings.insert_snippet(user_view, argument)
            else:
                user_view.sel().clear()
                user_view.show_at_center(result.end())
                user_view.sel().add(result.end() + 2)

    def do_linting(self):
        """Highlight all unknown settings keys."""
        unknown_regions = None
        if (
            self.known_settings
            # file_name maybe None if self.known_settings is None
            and USER_PATH in self.view.file_name()
            and get_setting('settings.linting')
        ):
            unknown_regions = [
                region for region in self.view.find_by_selector(KEY_SCOPE)
                if self.view.substr(region) not in self.known_settings
            ]

        if unknown_regions:
            styles = get_setting(
                'settings.highlight_styles',
                ['DRAW_SOLID_UNDERLINE', 'DRAW_NO_FILL', 'DRAW_NO_OUTLINE'])
            self.view.add_regions(
                'unknown_settings_keys',
                unknown_regions,
                scope=get_setting('settings.highlight_scope', "text"),
                icon='dot',
                flags=style_flags_from_list(styles)
            )
        else:
            self.view.erase_regions('unknown_settings_keys')


# Some hooks are not available to ViewEventListeners,
# which is why we need an EventListener as well.
class GlobalSettingsListener(sublime_plugin.EventListener):

    def _find_view_event_listener(self, view):
        if not SettingsListener.is_applicable(view.settings()):
            # speed up?
            return None
        for listener in sublime_plugin.event_listeners_for_view(view):
            if isinstance(listener, SettingsListener):
                return listener
        return None

    def on_post_text_command(self, view, command_name, args):
        if command_name == 'hide_auto_complete':
            listener = self._find_view_event_listener(view)
            if listener:
                listener.is_completing_key = False
        elif command_name in ('commit_completion', 'insert_best_completion'):
            listener = self._find_view_event_listener(view)
            if not (listener and listener.is_completing_key):
                return

            listener.is_completing_key = False
            sel = view.sel()
            if len(sel) != 1:
                # unclear what to do, so just do nothing
                return
            point = sel[0].begin()
            key_region = get_last_key_region(view, point)
            if key_region:
                key = view.substr(key_region)
                l.debug("showing popup after inserting key completion for %r", key)
                listener.show_popup_for(key_region)

    def on_post_save(self, view):
        listener = self._find_view_event_listener(view)
        if listener:
            listener.known_settings.trigger_settings_reload()
