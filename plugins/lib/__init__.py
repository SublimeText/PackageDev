import functools
import logging

import sublime

SETTINGS_FILE = "PackageDev.sublime-settings"

logger = logging.getLogger(__name__)


def package_settings():
    """Return global package settings object or load it first if required."""
    try:
        return package_settings.settings
    except AttributeError:
        logger.debug("Loading %s", SETTINGS_FILE)
        package_settings.settings = sublime.load_settings(SETTINGS_FILE)
        return package_settings.settings


def get_setting(key, default=None):
    return package_settings().get(key, default)


def inhibit_word_completions(func):
    """Decorator that inhibits ST's word completions if non-None value is returned."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        return (ret, sublime.INHIBIT_WORD_COMPLETIONS) if ret is not None else None

    return wrapper


def path_is_relative_to(path, *other):
    """Check whether a `pathlib.Path` is relative to another Path-like.

    Backport of Python 3.9's `pathlib.PurePath.is_relative_to`.
    """
    try:
        path.relative_to(*other)
        return True
    except ValueError:
        return False
