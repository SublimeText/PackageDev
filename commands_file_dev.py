import sublime_plugin
import os

from sublime import packages_path

from sublime_lib import path


tpl = """[
    { "caption": "${1:My Caption for the Comand Palette}", "command": "${2:my_command}" }$0
]"""

PLUGIN_NAME = os.getcwdu().replace(packages_path(), '')[1:]

SYNTAX_DEF = "Packages/%s/Support/Syntax Definitions/Sublime Commands.tmLanguage" % PLUGIN_NAME


class NewCommandsFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.run_command('insert_snippet', {'contents': tpl})
        v.settings().set('default_dir', path.root_at_packages('User'))
        v.set_syntax_file(SYNTAX_DEF)


