from xml.etree import ElementTree as ET

import sublime
import sublime_plugin

from .lib.sublime_lib.view import has_file_ext, get_text, clear
from .lib import syntax_paths

__all__ = (
    'GenerateSnippetFromRawSnippetCommand',
    'NewRawSnippetFromSnippetCommand',
)


SNIPPET_TEMPLATE = """<snippet>
    <content><![CDATA[$1]]></content>
    <tabTrigger>${2:tab_trigger}</tabTrigger>
    <scope>${3:source.base_scope}</scope>
    <!-- <description></description> -->
</snippet>""".replace("    ", "\t")  # always use tabs in snippets


class GenerateSnippetFromRawSnippetCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.match_selector(0, 'source.sublime.snippet')

    def run(self, edit):
        content = get_text(self.view)
        clear(self.view)
        self.view.run_command('insert_snippet', {'contents': SNIPPET_TEMPLATE})
        self.view.set_syntax_file(syntax_paths.SNIPPET)
        # Insert existing contents into CDATA section. We rely on the fact
        # that Sublime will place the first selection in the first field of
        # the newly inserted snippet.
        self.view.insert(edit, self.view.sel()[0].begin(), content)
        self.view.run_command("next_field")


class NewRawSnippetFromSnippetCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return has_file_ext(self.view, 'sublime-snippet')

    def run(self, edit):
        snippet = get_text(self.view)
        contents = ET.fromstring(snippet).findtext(".//content")
        v = self.view.window().new_file()
        v.run_command('insert', {'contents': contents})
        v.set_syntax_file(syntax_paths.SNIPPET_RAW)
