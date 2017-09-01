import logging

import sublime
import sublime_plugin

SETTINGS_FILE = "PackageDev.sublime-settings"

l = logging.getLogger(__name__)


def package_settings():
    """Return global package settings object or load it first if required."""
    try:
        return package_settings.settings
    except AttributeError:
        l.debug("Loading %s", SETTINGS_FILE)
        package_settings.settings = sublime.load_settings(SETTINGS_FILE)
        return package_settings.settings


def get_setting(key, default=None):
    return package_settings().get(key, default)


def sorted_completions(completions):
    """Sort completions case insensitively."""
    return list(sorted(completions, key=lambda x: x[0].lower()))


def find_view_event_listener(view, cls):
    if not cls.is_applicable(view.settings()):
        # speed up?
        return None
    for listener in sublime_plugin.event_listeners_for_view(view):
        # We don't use isinstance because we don't want a subclass
        if type(listener) is cls:
            return listener
    return None
