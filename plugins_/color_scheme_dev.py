import functools
import logging
import re

import sublime
import sublime_plugin

from sublime_lib import ResourcePath

from .lib.scope_data import completions_from_prefix
from .lib import syntax_paths

__all__ = (
    'ColorSchemeCompletionsListener',
    'PackagedevEditSchemeCommand',
)

SCHEME_TEMPLATE = """\
{
  // http://www.sublimetext.com/docs/3/color_schemes.html
  "variables": {
    // "green": "#FF0000",
  },
  "globals": {
    // "foreground": "var(green)",
  },
  "rules": [
    {
      // "scope": "string",
      // "foreground": "#00FF00",
    },
  ],
}""".replace("  ", "\t")

VARIABLES = [
    ("--background\tbuiltin color", "--background"),
    ("--foreground\tbuiltin color", "--foreground"),
    ("--accent\tbuiltin color", "--accent"),
    ("--bluish\tbuiltin color", "--bluish"),
    ("--cyanish\tbuiltin color", "--cyanish"),
    ("--greenish\tbuiltin color", "--greenish"),
    ("--orangish\tbuiltin color", "--orangish"),
    ("--pinkish\tbuiltin color", "--pinkish"),
    ("--purplish\tbuiltin color", "--purplish"),
    ("--redish\tbuiltin color", "--redish"),
    ("--yellowish\tbuiltin color", "--yellowish"),
]

logger = logging.getLogger(__name__)


def _inhibit_word_completions(func):
    """Decorator that inhibits ST's word completions if non-None value is returned."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        if ret is not None:
            return (ret, sublime.INHIBIT_WORD_COMPLETIONS)

    return wrapper


class ColorSchemeCompletionsListener(sublime_plugin.ViewEventListener):

    """Provide variable and scope name completions for color schemes.

    Extract completions from defined variables in the current file
    and determine scope completions based on our scope_data module.

    Also provide variable completions for themes.
    """

    @classmethod
    def applies_to_primary_view_only(cls):
        return False

    @classmethod
    def is_applicable(cls, settings):
        return settings.get('syntax') in (syntax_paths.COLOR_SCHEME, syntax_paths.THEME)

    def _line_prefix(self, point):
        _, col = self.view.rowcol(point)
        line = self.view.substr(self.view.line(point))
        return line[:col]

    def variable_completions(self, prefix, locations):
        variable_regions = self.view.find_by_selector("entity.name.variable.sublime-color-scheme, "
                                                      "entity.name.variable.sublime-theme")
        variables = set(self.view.substr(r) for r in variable_regions)
        sorted_variables = sorted(variables)
        logger.debug("Found %d variables to complete: %r", len(variables), sorted_variables)
        variable_completions = [("{}\tvariable".format(var), var) for var in sorted_variables]
        if self.view.match_selector(locations[0], "source.json.sublime.theme"):
            variable_completions += VARIABLES
        return variable_completions

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
        logger.debug("Full prefix: %r", real_prefix)
        if real_prefix is None:
            return None
        else:
            return completions_from_prefix(real_prefix)

    @_inhibit_word_completions
    def on_query_completions(self, prefix, locations):

        def verify_scope(selector, offset=0):
            """Verify scope for each location."""
            return all(self.view.match_selector(point + offset, selector)
                       for point in locations)

        if (
            verify_scope("meta.function-call.var.sublime-color-scheme")
            or (verify_scope("meta.function-call.var.sublime-color-scheme", -1)
                and verify_scope("punctuation.definition.string.end.json"))
        ):
            return self.variable_completions(prefix, locations)

        elif verify_scope("meta.scope-selector.sublime"):
            return self.scope_completions(prefix, locations)

        else:
            return None


class PackagedevEditSchemeCommand(sublime_plugin.WindowCommand):

    """Like syntax-specific settings but for the currently used color scheme."""

    def run(self):
        view = self.window.active_view()
        if not view:
            return

        # Be lazy here and don't consider invalid values
        scheme_setting = view.settings().get('color_scheme')
        if '/' not in scheme_setting:
            scheme_path = ResourcePath.glob_resources(scheme_setting)[0]
        else:
            scheme_path = ResourcePath(scheme_setting)

        self.window.run_command(
            'edit_settings',
            {
                "base_file": '/'.join(("${packages}",) + scheme_path.parts[1:]),
                "user_file": "${packages}/User/" + scheme_path.stem + '.sublime-color-scheme',
                "default": SCHEME_TEMPLATE,
            },
        )
