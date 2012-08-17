import uuid

import sublime_plugin

from sublime_lib.path import root_at_packages
from sublime_lib.view import in_one_edit


BASE_SYNTAX_LANGUAGE = 'Packages/AAAPackageDev/Support/Sublime Text Syntax Def (%s).tmLanguage'


# XXX: Move this to a txt file. Let user define his own under User too.
boilerplates = dict(
    json="""{ "name": "${1:Syntax Name}",
  "scopeName": "source.${2:syntax_name}",
  "fileTypes": ["$3"],
  "patterns": [$0
  ],
  "uuid": "%s"
}""",
    yaml="""---
name: ${1:Syntax Name}
scopeName: source.${2:syntax_name}
fileTypes: [$3]
uuid: %s

patterns:
- $0
..."""
)


class NewSyntaxDefCommand(object):
    """Creates a new syntax definition file for Sublime Text with some
    boilerplate text.
    """
    typ = ""

    def run(self):
        target = self.window.new_file()
        target.run_command('new_%s_syntax_def_to_buffer' % self.typ)


class NewJsonSyntaxDefCommand(NewSyntaxDefCommand, sublime_plugin.WindowCommand):
    typ = "json"


class NewYamlSyntaxDefCommand(NewSyntaxDefCommand, sublime_plugin.WindowCommand):
    typ = "yaml"


class NewSyntaxDefToBufferCommand(object):
    """Inserts boilerplate text for syntax defs into current view.
    """
    typ = ""

    def is_enabled(self):
        # Don't mess up a non-empty buffer.
        return self.view.size() == 0

    def run(self, edit):
        self.view.settings().set('default_dir', root_at_packages('User'))
        self.view.settings().set('syntax', BASE_SYNTAX_LANGUAGE % self.typ.upper())

        with in_one_edit(self.view):
            self.view.run_command('insert_snippet', {'contents': boilerplates[self.typ] % uuid.uuid4()})


class NewJsonSyntaxDefToBufferCommand(NewSyntaxDefToBufferCommand, sublime_plugin.TextCommand):
    typ = "json"


class NewYamlSyntaxDefToBufferCommand(NewSyntaxDefToBufferCommand, sublime_plugin.TextCommand):
    typ = "yaml"
