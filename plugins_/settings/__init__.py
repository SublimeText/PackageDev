import html.parser
import logging
import os

import sublime
import sublime_plugin

from sublime_lib.flags import RegionOption

from ..lib import get_setting
from ..lib.weakmethod import WeakMethodProxy

from .region_math import (VALUE_SCOPE, KEY_SCOPE, KEY_COMPLETIONS_SCOPE,
                          get_key_region_at, get_last_key_region)
from .known_settings import KnownSettings, PREF_FILE

__all__ = (
    'SettingsListener',
    'GlobalSettingsListener',
)

POPUP_TEMPLATE = """
<body id="sublime-settings">
<style>
    html.light {{
        --html-background: color(var(--background) blend(black 91%));
        --border-color: color(var(--html-background) blend(black 95%));
    }}
    html.dark {{
        --html-background: color(var(--background) blend(white 93%));
        --border-color: color(var(--html-background) blend(white 95%));
    }}
    html, body {{
        margin: 0;
        padding: 0;
        background-color: var(--html-background);
        color: var(--foreground);
    }}
    h1, h2 {{
        border-bottom: 1px solid var(--border-color);
        font-weight: normal;
        margin: 0;
        padding: 0.5rem 0.6rem;
    }}
    h1 {{
        color: var(--orangish);
        font-size: 1.0rem;
    }}
    html.light h1 {{
        color: var(--redish);
    }}
    h2 {{
        color: color(var(--html-background) blend(var(--foreground) 30%));
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

PHANTOM_TEMPLATE = """
<body id="sublime-settings-edit">
<style>
    html, body {{
        margin: 0;
        padding: 0;
        background-color: transparent;
    }}
    a {{
        text-decoration: none;
    }}
</style>
{0}
</body>
"""

WIDGET_SETTINGS_NAMES = {
    "Console Input Widget",
    "Regex Format Widget",
    "Regex Replace Widget",
    "Regex Widget",
    "Widget",
}

# user package pattern
USER_PATH = "{0}Packages{0}User{0}".format(os.sep)

l = logging.getLogger(__name__)


def is_widget_file(filename):
    basename, ext = os.path.splitext(filename)
    return (
        ext == ".sublime-settings"
        and filename in WIDGET_SETTINGS_NAMES
        or any(filename.startswith(name + " - ") for name in WIDGET_SETTINGS_NAMES)
    )


class SettingsListener(sublime_plugin.ViewEventListener):

    is_completing_key = False

    @classmethod
    def applies_to_primary_view_only(cls):
        return False

    @classmethod
    def is_applicable(cls, settings):
        """Enable the listener for Sublime Settings syntax only."""
        syntax = settings.get('syntax') or ""
        return (syntax.endswith("/Sublime Text Settings.sublime-syntax")
                or syntax.endswith("/Sublime Text Project.sublime-syntax"))

    def __init__(self, view):
        """Initialize view event listener object."""
        # Need this "hack" to allow reloading of the module,
        # because `super` tries to use the old reference (I think?).
        # See also https://lists.gt.net/python/python/139992
        sublime_plugin.ViewEventListener.__init__(self, view)

        filepath = view.file_name()
        l.debug("initializing SettingsListener for %r", view.file_name())

        is_widget_file(filepath)
        self.known_settings = None
        if filepath:
            filename = os.path.basename(filepath)
            if filepath.endswith(".sublime-project") or is_widget_file(filename):
                self.known_settings = KnownSettings(PREF_FILE)
            elif filepath.endswith(".sublime-settings"):
                self.known_settings = KnownSettings(filename)

        if self.known_settings:
            self.known_settings.add_on_loaded(self.do_linting)
        else:
            l.error("Not a Sublime Text Settings or Project file: %r", filepath)

        self.phantom_set = sublime.PhantomSet(self.view, "sublime-settings-edit")
        if self._is_base_settings_view():
            self.build_phantoms()

    def __del__(self):
        l.debug("deleting SettingsListener instance for %r", self.view.file_name())
        self.view.erase_regions('unknown_settings_keys')
        self.phantom_set.update([])

    def on_modified_async(self):
        """Sublime Text modified event handler to update linting."""
        self.do_linting()
        if self._is_base_settings_view():
            # This may only occur for unpacked packages
            self.build_phantoms()

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
            self.is_completing_key = False
            if self.view.match_selector(point, VALUE_SCOPE):
                completions_aggregator = self.known_settings.value_completions
            elif self.view.match_selector(point, KEY_COMPLETIONS_SCOPE):
                completions_aggregator = self.known_settings.key_completions
                self.is_completing_key = True
            else:
                return None
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
            location=location,
            max_width=window_width,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY | sublime.COOPERATE_WITH_AUTO_COMPLETE
        )

    def on_navigate(self, href):
        """Popup navigation event handler."""
        command, _, argument = href.partition(":")
        argument = html.parser.HTMLParser().unescape(argument)

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
        file_name = self.view.file_name() or ""
        if (
            self.known_settings
            and (USER_PATH in file_name
                 or file_name.endswith(".sublime-project"))
            and get_setting('settings.linting')
        ):
            unknown_regions = [
                region for region in self.view.find_by_selector(KEY_SCOPE)
                if self.view.substr(region) not in self.known_settings
            ]

        if unknown_regions:
            styles = get_setting(
                'settings.highlight_styles',
                ['DRAW_SOLID_UNDERLINE', 'DRAW_NO_FILL', 'DRAW_NO_OUTLINE']
            )
            self.view.add_regions(
                'unknown_settings_keys',
                unknown_regions,
                scope=get_setting('settings.highlight_scope', "text"),
                icon='dot',
                flags=RegionOption(*styles)
            )
        else:
            self.view.erase_regions('unknown_settings_keys')

    def build_phantoms(self):
        """Add links to side-by-side base file for editing this setting in the user file."""
        if self.view.is_loading():
            sublime.set_timeout(self.build_phantoms, 20)
            return
        l.debug("Building phantom set for view %r", self.view.file_name())
        key_regions = self.view.find_by_selector(KEY_SCOPE)
        phantoms = []
        for region in key_regions:
            key_name = self.view.substr(region)
            phantom_region = sublime.Region(region.end() + 1)  # before colon
            content = "<a href=\"edit:{0}\">✏</a>".format(html.escape(key_name))
            phantoms.append(sublime.Phantom(
                region=phantom_region,
                content=PHANTOM_TEMPLATE.format(content),
                layout=sublime.LAYOUT_INLINE,
                # use weak reference for callback
                # to allow for phantoms to be cleaned up in __del__
                on_navigate=WeakMethodProxy(self.on_navigate),
            ))
        l.debug("Made %d phantoms", len(phantoms))

        self.phantom_set.update(phantoms)

    def _is_base_settings_view(self):
        return self.view.settings().get('edit_settings_view') == 'base'


# Some hooks are not available to ViewEventListeners,
# which is why we need an EventListener as well.
class GlobalSettingsListener(sublime_plugin.EventListener):

    def on_post_text_command(self, view, command_name, args):
        if command_name == 'hide_auto_complete':
            listener = sublime_plugin.find_view_event_listener(view, SettingsListener)
            if listener:
                listener.is_completing_key = False
        elif command_name in ('commit_completion', 'insert_best_completion'):
            listener = sublime_plugin.find_view_event_listener(view, SettingsListener)
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
        listener = sublime_plugin.find_view_event_listener(view, SettingsListener)
        if listener and listener.known_settings:
            listener.known_settings.trigger_settings_reload()
