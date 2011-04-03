import sublime, sublime_plugin

from sublime_lib.view import has_file_ext

from xml.etree import ElementTree as ET


TPL = """<snippet>
    <content><![CDATA[%s]]></content>
    <tabTrigger>${1:tab_trigger}</tabTrigger>
    <scope>${2:source.name}</scope>
</snippet>"""


class NewRawSnippetCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('syntax', 'Packages/AAAPackageDev/Support/Sublime Snippet (Raw).tmLanguage')


class GenerateSnippetFromRawSnippetCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.match_selector(0, 'source.sublimesnippetraw'):
            new_snippet = TPL % self.view.substr(sublime.Region(0, self.view.size()))
            self.view.replace(edit, sublime.Region(0, self.view.size()), new_snippet)
            self.view.settings().set('syntax', 'Packages/XML/XML.tmLanguage')


class GenerateRawSnippetFromSnippetCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return has_file_ext(self.view, 'sublime-snippet')

    def run(self, edit):
        snippet = self.view.substr(sublime.Region(0, self.view.size()))
        contents = ET.fromstring(snippet).findtext(".//content")
        v = self.view.window().new_file()
        v.insert(edit, 0, contents)
        v.settings().set('syntax', 'Packages/AAAPackageDev/Support/Sublime Snippet (Raw).tmLanguage')