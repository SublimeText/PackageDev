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


DEFAULT_VALUE = ["rss", "sublime-snippet", "vcproj", "tmLanguage", "tmTheme", "tmSnippet",
                 "tmPreferences", "dae"]
MODIFIED_VALUE = ["rss", "vcproj", "tmLanguage", "tmTheme", "tmSnippet", "dae"]

# Encode ST build and date of last change (of this file) into the bootstrap value.
# I'm not sure what exactly I'm gonna do with it, so just include info I might find useful later.
BOOTSTRAP_VALUE = [3126, 2017, 3, 13]


def plugin_loaded():
    settings = sublime.load_settings("XML.sublime-settings")

    if settings.get('hidden_extensions') == DEFAULT_VALUE:
        settings.set('hidden_extensions', MODIFIED_VALUE)
        settings.set('package_dev.bootstrapped', BOOTSTRAP_VALUE)
        sublime.save_settings("XML.sublime-settings")

        print("[PackageDev] Bootstrapped XML's `hidden_extensions` setting")
