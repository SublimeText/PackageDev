import logging

import sublime


DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_LEVEL_NAME = logging.getLevelName(DEFAULT_LOG_LEVEL)


pl = logging.getLogger(__package__)
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt="[{name}] {levelname}: {message}", style='{')
handler.setFormatter(formatter)
pl.addHandler(handler)
pl.setLevel(DEFAULT_LOG_LEVEL)

l = logging.getLogger(__name__)


def _settings():
    return sublime.load_settings("PackageDev.sublime-settings")


def plugin_loaded():
    def on_settings_reload():
        cur_log_level_name = logging.getLevelName(pl.getEffectiveLevel())
        new_log_level_name = _settings().get('log_level', DEFAULT_LOG_LEVEL_NAME).upper()
        log_level = getattr(logging, new_log_level_name, DEFAULT_LOG_LEVEL)

        if new_log_level_name != cur_log_level_name:
            l.warning("Changing log level from %r to %r", cur_log_level_name, new_log_level_name)
            pl.setLevel(log_level)

    _settings().add_on_change(__name__, on_settings_reload)
    on_settings_reload()  # trigger on inital settings load, too


def plugin_unloaded():
    _settings().clear_on_change(__name__)
    pl.removeHandler(handler)
