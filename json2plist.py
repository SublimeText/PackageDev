import json
import plistlib
import os

def make_grammar(path_to_json_grammar):
    path, fname = os.path.split(path_to_json_grammar)
    plist_grammar_name, ext = os.path.splitext(fname)

    with open(path_to_json_grammar) as grammar_in_json:
        grammar = json.load(grammar_in_json)

    plist_dest_path = os.path.join(path, plist_grammar_name + ".tmLanguage")
    plistlib.writePlist(grammar, plist_dest_path)
