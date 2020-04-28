import sublime
import sublime_plugin

from sublime_lib import ResourcePath

__all__ = (
    'PackagedevEditThemeCommand',
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
