import functools
import logging
import re

import sublime
import sublime_plugin

from .lib.scope_data import completions_from_prefix
from .lib import syntax_paths

__all__ = (
    'ColorSchemeCompletionsListener',
)

l = logging.getLogger(__name__)


def _inhibit_word_completions(func):
    """Decorator that inhibits ST's word completions if non-None value is returned."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        if ret is not None:
            return (ret, sublime.INHIBIT_WORD_COMPLETIONS)

    return wrapper


class ColorSchemeCompletionsListener(sublime_plugin.ViewEventListener):

    @classmethod
    def is_applicable(cls, settings):
        return settings.get('syntax') == syntax_paths.COLOR_SCHEME

    def _line_prefix(self, point):
        _, col = self.view.rowcol(point)
        line = self.view.substr(self.view.line(point))
        return line[:col]

    def variable_completions(self, prefix, locations):
        variable_regions = self.view.find_by_selector("entity.name.variable.sublime-color-scheme")
        variables = set(self.view.substr(r) for r in variable_regions)
        l.debug("Found %d variables to complete: %r", len(variables), sorted(variables))
        return sorted(("{}\tvariable".format(var), var) for var in variables)

    def _scope_prefix(self, locations):
        # Determine entire prefix
        prefixes = set()
        for point in locations:
            text = self._line_prefix(point)
            real_prefix = re.search(r'[\w.-]*$', text).group(0)  # may be zero-length
            prefixes.add(real_prefix)

        if len(prefixes) > 1:
            return None
        else:
            return next(iter(prefixes))

    def scope_completions(self, prefix, locations):
        real_prefix = self._scope_prefix(locations)
        if not real_prefix:
            return None
        else:
            return completions_from_prefix(real_prefix)

    @_inhibit_word_completions
    def on_query_completions(self, prefix, locations):

        def verify_scope(selector, offset=0):
            """Verify scope for each location."""
            return all(self.view.match_selector(point + offset, selector)
                       for point in locations)

        if verify_scope("meta.function-call.var.sublime-color-scheme"):
            return self.variable_completions(prefix, locations)

        elif verify_scope("meta.scope-selector.sublime"):
            return self.scope_completions(prefix, locations)

        else:
            return None
