import sublime, sublime_plugin

from sublime_lib.view import has_file_ext

from xml.etree import ElementTree as ET


TPL = """<snippet>
    <content><![CDATA[$1]]></content>
    <tabTrigger>${2:tab_trigger}</tabTrigger>
    <scope>${3:source.name}</scope>
</snippet>"""


class NewRawSnippetCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('syntax', 'Packages/AAAPackageDev/Support/Sublime Snippet (Raw).tmLanguage')


class GenerateSnippetFromRawSnippetCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.match_selector(0, 'source.sublimesnippetraw')

    def run(self, edit):
        content = self.view.substr(sublime.Region(0, self.view.size()))
        self.view.replace(edit, sublime.Region(0, self.view.size()), '')
        self.view.run_command("insert_snippet", { "contents": TPL })
        self.view.settings().set('syntax', 'Packages/XML/XML.tmLanguage')
        self.view.insert(edit, self.view.sel()[0].begin(), content)


class NewRawSnippetFromSnippetCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return has_file_ext(self.view, 'sublime-snippet')

    def run(self, edit):
        snippet = self.view.substr(sublime.Region(0, self.view.size()))
        contents = ET.fromstring(snippet).findtext(".//content")
        v = self.view.window().new_file()
        v.insert(edit, 0, contents)
        v.settings().set('syntax', 'Packages/AAAPackageDev/Support/Sublime Snippet (Raw).tmLanguage')