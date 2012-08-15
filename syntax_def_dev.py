import uuid

import sublime_plugin

from sublime_lib.path import root_at_packages
from sublime_lib.view import in_one_edit


JSON_TMLANGUAGE_SYNTAX = 'Packages/AAAPackageDev/Support/Sublime Text Syntax Def (JSON).tmLanguage'


# XXX: Move this to a txt file. Let user define his own under User too.
def get_json_syntax_def_boilerplate():
    JSON_TEMPLATE = """{ "name": "${1:Syntax Name}",
  "scopeName": "source.${2:syntax_name}",
  "fileTypes": ["$3"],
  "patterns": [$0
  ],
  "uuid": "%s"
}"""
    return JSON_TEMPLATE % uuid.uuid4()


class NewJsonSyntaxDefCommand(sublime_plugin.WindowCommand):
    """Creates a new syntax definition file for Sublime Text in JSON format
    with some boilerplate text.
    """
    def run(self):
        target = self.window.new_file()

        target.settings().set('default_dir', root_at_packages('User'))
        target.settings().set('syntax', JSON_TMLANGUAGE_SYNTAX)

        target.run_command('insert_snippet',
                           {'contents': get_json_syntax_def_boilerplate()})


class NewJsonSyntaxDefFromBufferCommand(sublime_plugin.TextCommand):
    """Inserts boilerplate text for syntax defs into current view.
    """
    def is_enabled(self):
        # Don't mess up a non-empty buffer.
        return self.view.size() == 0

    def run(self, edit):
        self.view.settings().set('default_dir', root_at_packages('User'))
        self.view.settings().set('syntax', JSON_TMLANGUAGE_SYNTAX)

        with in_one_edit(self.view):
            self.view.run_command('insert_snippet',
                                  {'contents': get_json_syntax_def_boilerplate()})
