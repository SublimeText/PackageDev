from collections import OrderedDict
import logging
import json
import re
import itertools

import sublime
import sublime_plugin

from ..lib import sorted_completions
from .commandinfo import (
    get_command_name,
    get_builtin_command_meta_data,
    get_builtin_commands,
    iter_python_command_classes,
    get_args_from_command_name
)

__all__ = (
    "SublimeTextCommandCompletionPythonListener",
    "SublimeTextCommandArgsCompletionListener",
    "SublimeTextCommandArgsCompletionPythonListener",
    "SublimeTextCommandCompletionListener",
)

l = logging.getLogger(__name__)


def _escape_in_snippet(v):
    return v.replace("}", "\\}").replace("$", "\\$")


def create_args_snippet_from_command_args(command_args, quote_char='"', for_json=True):
    """Create an argument snippet to insert from the arguments to run a command.

    Parameters:
        command_args (dict)
            The arguments with their default value.
        quote_char (str)
            Which char should be used for string quoting.
        for_json (bool)
            Whether it should be done for a json or a python file.


    Returns (str)
        The formatted entry to insert into the sublime text package
        file.
    """
    counter = itertools.count(1)

    def make_snippet_item(k, v):
        if v is not None:
            if isinstance(v, str):
                v = '{q}${{{i}:{v}}}{q}'.format(i=next(counter),
                                                v=_escape_in_snippet(v),
                                                q=quote_char)
            else:
                if for_json:
                    dumps = json.dumps(v)
                else:  # python
                    dumps = repr(v)
                v = '${{{i}:{v}}}'.format(i=next(counter), v=_escape_in_snippet(dumps))
        else:
            v = '${i}'.format(i=next(counter))
        return '{q}{k}{q}: {v}'.format(k=k, v=v, q=quote_char)

    keys = iter(command_args)
    if not isinstance(command_args, OrderedDict):
        keys = sorted(keys)
    snippet_items = (make_snippet_item(k, command_args[k]) for k in keys)
    if for_json:
        args_content = ",\n\t".join(snippet_items)
        args_snippet = '"args": {{\n\t{0}\n}},$0'.format(args_content)
    else:
        args_content = ", ".join(snippet_items)
        args_snippet = '{{{0}}}'.format(args_content)
    return args_snippet


class SublimeTextCommandCompletionListener(sublime_plugin.EventListener):

    @staticmethod
    def _create_completion(c):
        name = get_command_name(c)
        module = c.__module__
        package = module.split(".")[0]
        show = "{name}\t{package}".format(**locals())
        return show, name

    def on_query_completions(self, view, prefix, locations):
        keymap_scope = "source.json.sublime meta.command-name"
        loc = locations[0]
        if not view.score_selector(loc, keymap_scope):
            return
        command_classes = iter_python_command_classes()

        completions = set()
        completions.update((c + "\tbuilt-in", c) for c in get_builtin_commands())
        completions.update(self._create_completion(c) for c in command_classes)
        return sorted_completions(completions), sublime.INHIBIT_WORD_COMPLETIONS


class SublimeTextCommandCompletionPythonListener(sublime_plugin.EventListener):

    _RE_LINE_BEFORE = re.compile(
        r"(?P<callervar>\w+)\s*\.\s*run_command\s*\("
        r"\s*['\"]\w*$",
        re.MULTILINE
    )

    @staticmethod
    def _create_builtin_completion(c):
        meta = get_builtin_command_meta_data()
        show = ("{c}\t({stype}) built-in"
                .format(c=c, stype=meta[c].get("command_type", " ")[:1].upper()))
        return show, c

    @staticmethod
    def _create_completion(c):
        name = get_command_name(c)
        module = c.__module__
        package = module.split(".")[0]
        if issubclass(c, sublime_plugin.TextCommand):
            stype = "T"
        elif issubclass(c, sublime_plugin.WindowCommand):
            stype = "W"
        elif issubclass(c, sublime_plugin.ApplicationCommand):
            stype = "A"
        else:
            stype = "?"

        show = "{name}\t({stype}) {package}".format(**locals())
        return show, name

    def on_query_completions(self, view, prefix, locations):
        loc = locations[0]
        python_arg_scope = (
            "source.python meta.function-call.python "
            "meta.function-call.arguments.python string.quoted"
        )
        if not view.score_selector(loc, python_arg_scope):
            return
        if sublime.packages_path() not in (view.file_name() or ""):
            return

        before_region = sublime.Region(view.line(loc).a, loc)
        lines = view.line(sublime.Region(view.line(locations[0]).a - 1, loc))
        before_region = sublime.Region(lines.a, loc)
        before = view.substr(before_region)
        m = self._RE_LINE_BEFORE.search(before)
        if not m:
            return
        # get the command type
        caller_var = m.group('callervar')
        if "view" in caller_var or caller_var == "v":
            command_type = 'text'
        elif caller_var == "sublime":
            command_type = 'app'
        else:
            # window.run_command allows all command types
            command_type = ''

        command_classes = iter_python_command_classes(command_type)
        completions = set()
        completions.update(
            self._create_builtin_completion(c)
            for c in get_builtin_commands(command_type)
        )
        completions.update(self._create_completion(c) for c in command_classes)
        return sorted_completions(completions), sublime.INHIBIT_WORD_COMPLETIONS


class SublimeTextCommandArgsCompletionListener(sublime_plugin.EventListener):

    _default_args = [("args\targuments", '"args": {\n\t"$1": "$2"$0\n},')]
    _st_insert_arg_scope = (
        "("
        "("
        + ", ".join("source.json.sublime.{}".format(suffix)
                    for suffix in ("commands", "keymap", "macro", "menu", "mousemap"))
        + ")"
        " & "
        "meta.sequence.json meta.mapping.json"
        ")"
        "- string "
        "- comment "
        "- meta.value.json "
        "- meta.mapping.json meta.mapping.json "
        "- meta.sequence.json meta.sequence.json "
    )
    _RE_COMMAND_SEARCH = re.compile(r'\"command\"\s*\:\s*\"(\w+)\"')

    def on_query_completions(self, view, prefix, locations):
        if not view.score_selector(locations[0], self._st_insert_arg_scope):
            return
        # extract the line and the line above to search for the command
        lines_reg = view.line(sublime.Region(view.line(locations[0]).a - 1, locations[0]))
        lines = view.substr(lines_reg)

        results = self._RE_COMMAND_SEARCH.findall(lines)
        if not results:
            return self._default_args

        command_name = results[-1]
        l.debug("building args completions for command %r", command_name)
        command_args = get_args_from_command_name(command_name)
        if not command_args:
            return self._default_args
        args = create_args_snippet_from_command_args(command_args, for_json=True)

        completions = [("args\tauto-detected arguments", args)]
        return completions


class SublimeTextCommandArgsCompletionPythonListener(sublime_plugin.EventListener):

    _default_args_dict = {q: [("args\targuments", "{{{q}$1{q}: {q}$2{q}$0}}".format(q=q))]
                          for q in "'\""}
    _RE_LINE_BEFORE = re.compile(
        r"\w+\s*\.\s*run_command\s*\("
        r"\s*(['\"])(\w+)\1,\s*\w*$"
    )

    def on_query_completions(self, view, prefix, locations):
        loc = locations[0]
        python_arg_scope = "source.python meta.function-call.python"
        if not view.score_selector(loc, python_arg_scope):
            return
        if sublime.packages_path() not in (view.file_name() or ""):
            return

        before_region = sublime.Region(view.line(loc).a, loc)
        before = view.substr(before_region)
        m = self._RE_LINE_BEFORE.search(before)
        if not m:
            return
        quote_char, command_name = m.groups()
        l.debug("building args completions for command %r", command_name)

        command_args = get_args_from_command_name(command_name)
        if command_args is None:
            return self._default_args_dict[quote_char]
        args = create_args_snippet_from_command_args(command_args, quote_char, for_json=False)

        completions = [("args\tauto-detected arguments", args)]
        return completions
