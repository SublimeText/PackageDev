import sublime, sublime_plugin


COMPLETIONS_SYNTAX_DEF = "Packages/AAAPackageDev/Support/Sublime Completions.tmLanguage"
TPL = """{
    "scope": "source.${1:off}",

    "completions": [
    $0
    ]
}"""


class NewCompletionsCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.run_command('insert_snippet', {"contents": TPL})
        v.settings().set('syntax', COMPLETIONS_SYNTAX_DEF)
        v.settings().set('default_dir', 'Packages/User')