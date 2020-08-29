"""Bootstrap the 'hidden_extensions' setting for the XML syntax.

The XML package includes a `XML.sublime-settings` file
that sets `hidden_extensions` to include some of the extensions
we want to highlight with our package.
There is currently no other way to override this,
so we manually override this extension list
in a User settings file with a plugin.

See also:
  https://github.com/sublimehq/Packages/issues/823
  https://github.com/SublimeTextIssues/Core/issues/1326
"""
import sublime
from sublime_lib import ResourcePath

__all__ = [
    "plugin_loaded",
]

DEFAULT_VALUE = ["rss", "sublime-snippet", "vcproj", "tmLanguage", "tmTheme", "tmSnippet",
                 "tmPreferences", "dae"]
MODIFIED_VALUE = ["rss", "vcproj", "tmLanguage", "tmTheme", "tmSnippet", "dae"]

# Encode ST build and date of last change (of this file) into the bootstrap value.
# I'm not sure what exactly I'm gonna do with it, so just include info I might find useful later.
BOOTSTRAP_VALUE = [3126, 2017, 3, 13]


def override_extensions(expected, modified):
    settings = sublime.load_settings("XML.sublime-settings")

    if settings.get('hidden_extensions') == expected:
        settings.set('hidden_extensions', modified)
        settings.set('package_dev.bootstrapped', BOOTSTRAP_VALUE)
        sublime.save_settings("XML.sublime-settings")

        print("[PackageDev] Bootstrapped XML's `hidden_extensions` setting")


def remove_override():
    settings = sublime.load_settings("XML.sublime-settings")
    if settings.get('package_dev.bootstrapped'):
        settings.erase('package_dev.bootstrapped')

        if settings.get('hidden_extensions') == MODIFIED_VALUE:
            settings.erase('hidden_extensions')
        print("[PackageDev] Unbootstrapped XML's `hidden_extensions` setting")
        sublime.save_settings("XML.sublime-settings")
        sublime.set_timeout(remove_file_if_empty, 2000)  # Give ST time to write the file


def remove_file_if_empty():
    path = ResourcePath("Packages/User/XML.sublime-settings").file_path()
    try:
        with path.open() as f:
            data = sublime.decode_value(f.read())
    except (FileNotFoundError, ValueError):
        pass
    else:
        if not data or len(data) == 1 and 'extensions' in data and not data['extensions']:
            path.unlink()
            print("[PackageDev] Removed now-empty XML.sublime-settings")


def plugin_loaded():
    version = int(sublime.version())
    if version < 3153:
        override_extensions(DEFAULT_VALUE, MODIFIED_VALUE)
    # "csproj" was added for 3153.
    # https://github.com/sublimehq/Packages/commit/4a3712b7e236f8c4b443282d97bad17f68df318c
    # Technically there was a change in 4050, but nobody should be using that anymore.
    # https://github.com/sublimehq/Packages/commit/7866273af18398bce324408ff23c7a22f30486c8
    elif version < 4075:
        override_extensions(DEFAULT_VALUE + ["csproj"], MODIFIED_VALUE + ["csproj"])
    elif version >= 4075:
        # The settings were move to the syntax file
        # https://github.com/sublimehq/Packages/commit/73b16ff196d3cbaf7df2cf5807fda6ab68a2434e
        remove_override()
