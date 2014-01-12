import sublime_plugin

from sublime_lib.path import root_at_packages, get_package_name


PLUGIN_NAME = get_package_name()

SETTINGS_SYNTAX = "Packages/%s/Syntax Definitions/Sublime Settings.tmLanguage" % PLUGIN_NAME
TPL = """{$0}"""


class NewSettingsCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir', root_at_packages('User'))
        v.settings().set('syntax', SETTINGS_SYNTAX)
        v.run_command('insert_snippet', {'contents': TPL})
