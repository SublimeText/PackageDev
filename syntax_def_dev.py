import sublime, sublime_plugin

import os
import json2plist
import uuid

from sublime_lib.view import has_file_ext
from sublime_lib.path import root_at_packages


THIS_PACKAGE_NAME = "AAAPackageDev"
THIS_PACKAGE_DEV_NAME = "XXX" + THIS_PACKAGE_NAME
DEBUG = os.path.exists(sublime.packages_path() + "/" + THIS_PACKAGE_DEV_NAME)

PATH_TO_JSON_TMLANGUAGE_SYNTAX_DEF = 'Packages/AAAPackageDev/Support//Sublime JSON Syntax Definition.tmLanguage'
PATH_TO_SUBLIME_KEY_MAP_SYNTAX_DEF = 'Packages/AAAPackageDev/Support/Sublime Key Map.tmLanguage'


# TODO: insert template as snippet, replace name with lowercased name.
def get_syntax_def_boilerplate():
    JSON_TEMPLATE = """{ "name": "${1:Syntax Name}",
  "scopeName": "source.${2:syntax_name}", 
  "fileTypes": ["$3"], 
  "patterns": [$0
  ],
  "uuid": "%s"
}"""

    actual_tmpl = JSON_TEMPLATE % str(uuid.uuid4())

    return actual_tmpl


# Ugly name so Sublime normalizes in a sane way.
class JsonToTmlanguage(sublime_plugin.TextCommand):
    """Takes a syntax definition in JSON and converts it to a .tmLanguage
    format (Plist) that Sublime Text understands.
    """

    def run(self, edit):
      path, fname = os.path.split(self.view.file_name())
      plist_grammar_name, ext = os.path.splitext(fname)

      if not ext.lower() == ".json-tmlanguage":
          sublime.error_message("~ AAAPackageDev Error ~\n\n"
                                "Not a valid extension. (Must be: json-tmLanguage)")
          return

      try:
          json2plist.make_grammar(self.view.file_name())
      except IOError as e:
          sublime.error_message(
                        "[AAAPackageDev] Error while converting to Plist.")
          return


class NewSyntaxDefCommand(sublime_plugin.WindowCommand):
    """Creates a new syntax definition file for Sublime Text in JSON format
    with some boilerplate text.
    """

    def run(self):
        # TODO: one_edit(view) context manager => Lib
        target = self.window.new_file()
        edit = target.begin_edit()
        target.settings().set("syntax", PATH_TO_JSON_TMLANGUAGE_SYNTAX_DEF)
        target.run_command('insert_snippet', {
                                                'contents':
                                                get_syntax_def_boilerplate()}
                                                )
        # target.insert(edit, 0, get_syntax_def_boilerplate())
        target.end_edit(edit)


class NewSyntaxDefFromBufferCommand(sublime_plugin.TextCommand):
    """Inserts boilerplate text for syntax defs into current view.
    """

    def run(self, edit):
        self.view.run_command('insert_snippet', {
                                                'contents':
                                                get_syntax_def_boilerplate()}
                                                )
        self.view.settings().set("syntax", PATH_TO_JSON_TMLANGUAGE_SYNTAX_DEF)
        # TODO: force extension for saving. (Used to be: force_extension)


class ApplyPackageDevSyntaxDef(sublime_plugin.EventListener):
    """Applies custom syntax definitions for several Sublime file types
    overriding the build-in behavior.
    """

    def on_load(self, view):
        if has_file_ext(view, '.sublime-keymap'):
            view.set_syntax_file('Packages/AAAPackageDev/Support/Sublime Key Map.tmLanguage')


class MakeTmlanguageCommand(sublime_plugin.WindowCommand):
    """Generates a ``.tmLanguage`` file from a ``.JSON-tmLanguage`` syntax def.
    """
    def is_enabled(self):
        return has_file_ext(self.window.active_view(), '.JSON-tmLanguage')

    def run(self, **kwargs):
        v = self.window.active_view()
        path = v.file_name()
        if not (os.path.exists(path) and has_file_ext(v, 'JSON-tmLanguage')):
            print "[AAAPackageDev] Not a valid JSON-tmLanguage file. (%s)" % path
            return

        build_cmd = root_at_packages("AAAPackageDev/Support/make_tmlanguage.py")
        file_regex = r"Error:\s+'(.*?)'\s+.*?\s+line\s+(\d+)\s+column\s+(\d+)"
        cmd = ["python", build_cmd, path]

        self.window.run_command("exec", {"cmd": cmd, "file_regex": file_regex})