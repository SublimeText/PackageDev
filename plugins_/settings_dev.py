import sublime_plugin

from .lib.sublime_lib.path import root_at_packages

__all__ = ('NewSettingsCommand',)

PACKAGE_NAME = __package__.split('.')[0]

SETTINGS_SYNTAX = ("Packages/%s/Package/Sublime Text Settings/Sublime Text Settings.sublime-syntax"
                   % PACKAGE_NAME)
TPL = '''\
{
    "$1": $0
}'''.replace(" " * 4, "\t")


class NewSettingsCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir', root_at_packages('User'))
        v.set_syntax_file(SETTINGS_SYNTAX)
        v.run_command('insert_snippet', {'contents': TPL})
