import sublime, sublime_plugin

import os
import json2plist
import uuid


THIS_PACKAGE_NAME = "AAAPackageDev"
THIS_PACKAGE_DEV_NAME = "XXX" + THIS_PACKAGE_NAME
DEBUG = os.path.exists(sublime.packages_path() + "/" + THIS_PACKAGE_DEV_NAME)

# TODO: root_at_packages_path(*leafs) => Lib
def build_path_relative_to_this_package(leaf):
    return os.path.join(sublime.packages_path(),
                        THIS_PACKAGE_NAME if not DEBUG else THIS_PACKAGE_DEV_NAME,
                        leaf)

# TODO: insert template as snippet, replace name with lowercased name.
def get_syntax_def_boilerplate():
    JSON_TEMPLATE = """{ "name": "${1:Untitled}",
  "scopeName": "source.${1/./\\l/}", 
  "fileTypes": ["ff", "fff"], 
  "patterns": [
      {"name": "keyword.control.${1/./\\l/}",
       "match": "\\\\b(if|while|for|return)\\\\b"
      },
      {"name": "string.quoted.double.${1/./\\l/}",
       "begin": "\\\"",
       "beginCaptures": {"0": {"name": "definition.string.quoted.double.${1/./\\l/}" }},
       "end": "\\\"",
       "patterns": [
            {"name": "constant.character.escape.${1/./\\l/}",
             "match": "\\\\."
            }
       ]
      } 
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

      # TODO: has_extension(view, ext) => Lib
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


class NewSyntaxDefCommand(sublime_plugin.TextCommand):
    """Creates a new syntax definition file for Sublime Text in JSON format
    with some boilerplate text.
    """

    def run(self, edit):
        # TODO: one_edit(view) context manager => Lib
        grammar_view = self.view.window().new_file()
        grammar_edit = grammar_view.begin_edit()
        grammar_view.settings().set("syntax", "Packages/JavaScript/JSON.tmLanguage")
        grammar_view.insert(grammar_edit, 0, get_syntax_def_boilerplate())
        grammar_view.end_edit(grammar_edit)


class NewSyntaxDefFromBufferCommand(sublime_plugin.TextCommand):
    """Inserts boilerplate text for syntax defs into current view.
    """

    def run(self, edit):
        self.view.insert(edit, self.view.size(), get_syntax_def_boilerplate())
        self.view.settings().set("syntax", "Packages/JavaScript/JSON.tmLanguage")
