import sys
import sublime_plugin

if sys.version_info < (3,):
    from sublime_lib.path import root_at_packages, get_package_name
else:
    from .sublime_lib.path import root_at_packages, get_package_name


tpl = """[
    { "caption": "${1:PackageName}: ${2:My Caption for the Command Palette}", "command": "${3:my_command}" }$0
]""".replace("    ", "\t")  # NOQA

PLUGIN_NAME = get_package_name()

SYNTAX_DEF = "Packages/%s/Syntax Definitions/Sublime Commands.tmLanguage" % PLUGIN_NAME


class NewCommandsFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.run_command('insert_snippet', {'contents': tpl})
        v.settings().set('default_dir', root_at_packages('User'))
        v.set_syntax_file(SYNTAX_DEF)
