import os

from sublime import packages_path
import sublime_plugin

from sublime_lib.path import root_at_packages

PLUGIN_NAME = os.getcwdu().replace(packages_path(), '')[1:]

COMPLETIONS_SYNTAX_DEF = "Packages/%s/Support/Syntax Definitions/Sublime Completions.tmLanguage" % PLUGIN_NAME
TPL = """{
    "scope": "source.${1:off}",

    "completions": [
        { "trigger": "${2:some_trigger}", "contents": "${3:Hint: Use f, ff and fff plus Tab inside here.}" }$0
    ]
}"""


class NewCompletionsCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.run_command('insert_snippet', {"contents": TPL})
        v.settings().set('syntax', COMPLETIONS_SYNTAX_DEF)
        v.settings().set('default_dir', root_at_packages('User'))
