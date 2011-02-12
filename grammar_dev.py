import sublime, sublime_plugin
import os
import json2plist
import subprocess
import uuid
import urllib

THIS_PACKAGE_NAME = "GrammarDev"
THIS_PACKAGE_DEV_NAME = "XXX" + THIS_PACKAGE_NAME
DEBUG = os.path.exists(sublime.packages_path() + "/" + THIS_PACKAGE_DEV_NAME)


def build_path_relative_to_this_package(leaf):
    return os.path.join(sublime.packages_path(),
                        THIS_PACKAGE_NAME if not DEBUG else THIS_PACKAGE_DEV_NAME,
                        leaf)

def get_new_syntax_content():
    JSON_TEMPLATE = """{ "name": "Untitled",  "scopeName": "source.untitled",  "fileTypes": ["ff", "fff"],  "patterns": [     { "name": "keyword.control.untitled",       "match": "\\\\b(if|while|for|return)\\\\b"     },
     { "name": "string.quoted.double.untitled",       "begin": "\\\"",       "beginCaptures": {         "0": { "name": "definition.string.quoted.double.untitled" }       },       "end": "\\\"",       "patterns": [          { "name": "constant.character.escape.untitled",            "match": "\\\\."          }        ]     }  ],  "uuid": "%s"}"""

    actualTmpl = JSON_TEMPLATE % str(uuid.uuid4())

    return actualTmpl


class GenerateGrammarFromJsonCommand(sublime_plugin.TextCommand):
    """
    Takes a syntax definition in json and converts it to a plist format that
    Sublime Text understands (Text Mate)
    """

    def run(self, edit, *args):
      path, fname = os.path.split(self.view.file_name())
      plist_grammar_name, ext = os.path.splitext(fname)

      if not ext.lower() == ".json-tmlanguage":
          sublime.error_message("~ GrammarDev ~\n\nNot a valid extension. (Must be: json-tmLanguage)")
          return

      try:
          json2plist.make_grammar(self.view.file_name())
      except IOError as e:
          sublime.error_message("ERROR: Error while converting to Plist.")
          return

class NewSyntaxDefCommand(sublime_plugin.TextCommand):
    """
    Creates a new syntax definition file for Sublime Text in json format with
    some boilerplate date filled in.
    """

    def run(self, edit, *args):
        grammar_view = self.view.window().new_file()
        grammar_edit = grammar_view.begin_edit()
        grammar_view.settings().set("syntax", buildPathRelativeToThisPackage("JSON tmLanguage.tmLanguage"))
        grammar_view.insert(grammar_edit, 0, get_new_syntax_content())
        grammar_view.end_edit(grammar_edit)


class GetSyntaxDefCommand(sublime_plugin.TextCommand):
    def run(self, edit, *args):
        self.view.settings().set("syntax", buildPathRelativeToThisPackage("JSON tmLanguage.tmLanguage"))
        self.view.insert(edit, self.view.size(), get_new_syntax_content())
