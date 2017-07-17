import sublime_plugin

from .lib.sublime_lib.path import root_at_packages

__all__ = ('NewCommandsFileCommand',)

tpl = """[
    { "caption": "${1:PackageName}: ${2:My Caption for the Command Palette}", "command": "${3:my_command}" }$0
]""".replace("    ", "\t")  # NOQA

PACKAGE_NAME = __package__.split('.')[0]

SYNTAX_DEF = "Packages/%s/Package/Sublime Text Commands/Sublime Commands.tmLanguage" % PACKAGE_NAME


class NewCommandsFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.run_command('insert_snippet', {'contents': tpl})
        v.settings().set('default_dir', root_at_packages('User'))
        v.set_syntax_file(SYNTAX_DEF)
