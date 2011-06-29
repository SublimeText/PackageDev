import sublime, sublime_plugin


SETTINGS_SYNTAX = 'Packages/AAAPackageDev/Support/Sublime Settings.tmLanguage'


TPL = """{$0}"""


class NewSettingsCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir', 'Packages/User')
        v.settings().set('syntax', SETTINGS_SYNTAX)
        v.run_command('insert_snippet', {'contents': TPL})
