import logging

import sublime
import sublime_plugin

from sublime_lib import ResourcePath

from .lib import syntax_paths
from .color_scheme_dev import inhibit_word_completions

__all__ = (
    'PackagedevEditThemeCommand',
    'ThemeCompletionsListener',
)

THEME_TEMPLATE = """\
{
  // http://www.sublimetext.com/docs/3/themes.html
  "variables": {
    // "font_face": "system",
  },
  "rules": [
  ],
}""".replace("  ", "\t")

logger = logging.getLogger(__name__)


class PackagedevEditThemeCommand(sublime_plugin.WindowCommand):

    """Like syntax-specific settings but for the currently used color scheme."""

    def run(self):
        theme_name = sublime.load_settings('Preferences.sublime-settings').get('theme')
        theme_path = ResourcePath(sublime.find_resources(theme_name)[0])
        self.window.run_command(
            'edit_settings',
            {
                "base_file": '/'.join(("${packages}",) + theme_path.parts[1:]),
                "user_file": "${packages}/User/" + theme_path.name,
                "default": THEME_TEMPLATE,
            },
        )


class ThemeCompletionsListener(sublime_plugin.ViewEventListener):

    """Provide completions for themes.

    Offer names of theme files to extend.
    Other completions are shared with color schemes
    and implemented in color_scheme_dev.py.
    """

    @classmethod
    def applies_to_primary_view_only(cls):
        return False

    @classmethod
    def is_applicable(cls, settings):
        return settings.get('syntax') in (syntax_paths.COLOR_SCHEME, syntax_paths.THEME)

    @inhibit_word_completions
    def on_query_completions(self, prefix, locations):
        if len(locations) != 1:
            return None
        point = locations[0]

        if self.view.match_selector(point, "meta.extends.sublime-theme"):
            return self.extends_completions()

    def extends_completions(self):
        resources = sublime.find_resources("*.sublime-theme")
        resources += sublime.find_resources("*.hidden-theme")
        names = {res.rsplit("/", 1)[-1] for res in resources}

        if self.view.file_name():
            names -= {ResourcePath.from_file_path(self.view.file_name()).name}
        
        sorted_names = sorted(names)
        logger.debug("Found %d themes to complete: %r", len(names), sorted_names)
        return [("{}\ttheme".format(name), name) for name in sorted_names]
