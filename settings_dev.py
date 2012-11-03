import os

from sublime import packages_path
import sublime_plugin

from sublime_lib.path import root_at_packages


PLUGIN_NAME = os.getcwdu().replace(packages_path(), '')[1:]

SETTINGS_SYNTAX = "Packages/%s/Support/Syntax Definitions/Sublime Settings.tmLanguage" % PLUGIN_NAME


TPL = """{$0}"""


class NewSettingsCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir', root_at_packages('User'))
        v.settings().set('syntax', SETTINGS_SYNTAX)
        v.run_command('insert_snippet', {'contents': TPL})
