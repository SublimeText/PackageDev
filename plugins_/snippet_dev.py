from xml.etree import ElementTree as ET

import sublime_plugin

from .lib.sublime_lib.view import has_file_ext, get_text, clear
from .lib import syntax_paths

__all__ = (
    'PackagedevSnippetFromRawSnippetCommand',
    'PackagedevRawSnippetFromSnippetCommand',
)

PACKAGE_NAME = __package__.split(".")[0]
SNIPPET_PATH = (
    "Packages/{}/Package/Sublime Text Snippet/Snippet.sublime-snippet"
    .format(PACKAGE_NAME)
)


def _insert_unindented(view, text):
    # circumvent auto-indentation with this method
    view.run_command('insert_snippet', {'contents': "$bla", 'bla': text})


class PackagedevSnippetFromRawSnippetCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.match_selector(0, "source.sublime.snippet")

    def run(self, edit):
        content = get_text(self.view)
        clear(self.view)
        self.view.run_command('insert_snippet', {'name': SNIPPET_PATH})

        # defuse CDATA end sequence with an undefined variable
        content = content.replace("]]>", "]]$UNDEFINED>")
        # Insert existing contents into CDATA section. We rely on the fact
        # that Sublime will place the first selection in the first field of
        # the newly inserted snippet.
        _insert_unindented(self.view, content)
        self.view.run_command('next_field')

        self.view.set_syntax_file(syntax_paths.SNIPPET)


class PackagedevRawSnippetFromSnippetCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return has_file_ext(self.view, 'sublime-snippet')

    def run(self, edit):
        snippet = get_text(self.view)
        content = ET.fromstring(snippet).findtext(".//content")
        content = content.replace("]]$UNDEFINED>", "]]>")  # undo defusing

        v = self.view.window().new_file()
        v.set_syntax_file(syntax_paths.SNIPPET_RAW)
        _insert_unindented(v, content)
