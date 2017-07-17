import sublime_plugin

from .lib.sublime_lib.path import root_at_packages

__all__ = ('NewCompletionsCommand',)

PACKAGE_NAME = __package__.split('.')[0]

COMPLETIONS_SYNTAX_DEF = ("Packages/%s/Package/"
                          "Sublime Text Completions/Sublime Completions.tmLanguage"
                          % PACKAGE_NAME)
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
