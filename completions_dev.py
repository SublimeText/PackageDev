import sys

import sublime_plugin

if sys.version_info < (3,):
    from sublime_lib.path import root_at_packages, get_package_name
else:
    from .sublime_lib.path import root_at_packages, get_package_name

PLUGIN_NAME = get_package_name()

COMPLETIONS_SYNTAX_DEF = ("Packages/%s/Syntax Definitions/Sublime Completions.tmLanguage"
                          % PLUGIN_NAME)
TPL = """{
    "scope": "source.${1:off}",

    "completions": [
        { "trigger": "${2:some_trigger}", "contents": "${3:Hint: Use f, ff and fff plus Tab inside here.}" }$0
    ]
}""".replace("    ", "\t")  # NOQA - line length


class NewCompletionsCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.run_command('insert_snippet', {"contents": TPL})
        v.set_syntax_file(COMPLETIONS_SYNTAX_DEF)
        v.settings().set('default_dir', root_at_packages('User'))
