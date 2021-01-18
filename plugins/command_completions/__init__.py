from collections import OrderedDict
import logging
import json
import re
import itertools

import sublime
import sublime_plugin

from ..lib import inhibit_word_completions
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

KIND_APPLICATION = (sublime.KIND_ID_FUNCTION, "A", "Application Command")
KIND_WINDOW = (sublime.KIND_ID_FUNCTION, "W", "Window Command")
KIND_TEXT = (sublime.KIND_ID_FUNCTION, "T", "Text Command")
KIND_MAP = {
    'application': KIND_APPLICATION,
    'window': KIND_WINDOW,
    'text': KIND_TEXT,
}
KIND_COMMAND = (sublime.KIND_ID_FUNCTION, "C", "Command")  # fallback
KIND_SNIPPET = sublime.KIND_SNIPPET

logger = logging.getLogger(__name__)


def _escape_in_snippet(v):
    return v.replace("}", "\\}").replace("$", "\\$")


def is_plugin(view):
    """Use some heuristics to determine whether a Python view shows a plugin.

    Or the console input widget, should it be using the Python syntax.
    """
    return (view.find("import sublime", 0, sublime.LITERAL) is not None
            or sublime.packages_path() in (view.file_name() or "")
            or view.settings().get('is_widget'))


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


def _builtin_completions(names):
    _, data = get_builtin_command_meta_data()
    for name in names:
        yield sublime.CompletionItem(
            trigger=name,
            annotation="built-in",
            completion=name,
            kind=KIND_MAP.get(data[name].get("command_type"), KIND_COMMAND),
            details=data[name].get('doc_string') or "",
            # TODO link to show full description
        )


def _plugin_completions(cmd_classes):
    for cmd_class in cmd_classes:
        name = get_command_name(cmd_class)
        module = cmd_class.__module__
        package_name = module.split(".")[0]
        if issubclass(cmd_class, sublime_plugin.TextCommand):
            kind = KIND_TEXT
        elif issubclass(cmd_class, sublime_plugin.WindowCommand):
            kind = KIND_WINDOW
        elif issubclass(cmd_class, sublime_plugin.ApplicationCommand):
            kind = KIND_APPLICATION
        else:
            kind = KIND_COMMAND

        yield sublime.CompletionItem(
            trigger=name,
            annotation=package_name,
            completion=name,
            kind=kind,
            details=(cmd_class.__doc__ or "").strip(),
            # TODO link to show full description
        )


def _create_completions(command_type=""):
    completions = []
    completions.extend(_builtin_completions(get_builtin_commands(command_type)))
    completions.extend(_plugin_completions(iter_python_command_classes(command_type)))
    logger.debug("Collected %d command completions", len(completions))
    return completions


class SublimeTextCommandCompletionListener(sublime_plugin.EventListener):

    @inhibit_word_completions
    def on_query_completions(self, view, prefix, locations):
        keymap_scope = "source.json.sublime meta.command-name"
        loc = locations[0]
        if not view.score_selector(loc, keymap_scope):
            return
        return _create_completions()


class SublimeTextCommandCompletionPythonListener(sublime_plugin.EventListener):

    _RE_LINE_BEFORE = re.compile(
        r"(?P<callervar>\w+)\s*\.\s*run_command\s*\("
        r"\s*['\"]\w*$",
        re.MULTILINE
    )

    @inhibit_word_completions
    def on_query_completions(self, view, prefix, locations):
        loc = locations[0]
        python_arg_scope = ("source.python meta.function-call.arguments.python string.quoted")
        if not view.score_selector(loc, python_arg_scope) or not is_plugin(view):
            return None

        before_region = sublime.Region(view.line(loc).a, loc)
        lines = view.line(sublime.Region(view.line(locations[0]).a - 1, loc))
        before_region = sublime.Region(lines.a, loc)
        before = view.substr(before_region)
        m = self._RE_LINE_BEFORE.search(before)
        if not m:
            return None
        # get the command type
        caller_var = m.group('callervar')
        logger.debug("caller_var: %s", caller_var)
        if "view" in caller_var or caller_var == "v":
            command_type = 'text'
        elif caller_var == "sublime":
            command_type = 'app'
        else:
            # window.run_command allows all command types
            command_type = ''

        return _create_completions(command_type)


class SublimeTextCommandArgsCompletionListener(sublime_plugin.EventListener):

    _default_args = [("args\targuments", '"args": {\n\t"$1": "$2"$0\n},')]
    _st_insert_arg_scope = (
        "("
        "  ("
        + ", ".join("source.json.sublime.{}".format(suffix)
                    for suffix in ("commands", "keymap", "macro", "menu", "mousemap"))
        + ")"
        "  & "
        "  meta.sequence meta.mapping"
        "  - meta.sequence meta.mapping meta.mapping"
        ")"
        "- string "
        "- comment "
        "- ("
        "    meta.value.json "
        "  | meta.mapping.json meta.mapping.json "
        "  | meta.sequence.json meta.sequence.json "
        "  - meta.menu.collection.sublime-menu"
        ")"
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
        logger.debug("building args completions for command %r", command_name)
        command_args = get_args_from_command_name(command_name)
        if not command_args:
            return self._default_args
        completion = create_args_snippet_from_command_args(command_args, for_json=True)

        return [sublime.CompletionItem(
            trigger="args",
            annotation="auto-detected",
            completion=completion,
            completion_format=sublime.COMPLETION_FORMAT_SNIPPET,
            kind=KIND_SNIPPET,
        )]


class SublimeTextCommandArgsCompletionPythonListener(sublime_plugin.EventListener):

    _default_args_dict = {
        c: sublime.CompletionItem(
            trigger="args",
            completion="{{{q}$1{q}: $0}}".format(q=c),
            completion_format=sublime.COMPLETION_FORMAT_SNIPPET,
            kind=KIND_SNIPPET,
        )
        for c in "'\""
    }
    _RE_LINE_BEFORE = re.compile(
        r"\w+\s*\.\s*run_command\s*\("
        r"\s*(['\"])(\w+)\1,\s*\w*$"
    )

    def on_query_completions(self, view, prefix, locations):
        loc = locations[0]
        python_arg_scope = "source.python meta.function-call.arguments.python,"
        if not view.score_selector(loc, python_arg_scope) or not is_plugin(view):
            return

        before_region = sublime.Region(view.line(loc).a, loc)
        before = view.substr(before_region)
        m = self._RE_LINE_BEFORE.search(before)
        if not m:
            return
        quote_char, command_name = m.groups()
        logger.debug("building args completions for command %r", command_name)

        command_args = get_args_from_command_name(command_name)
        if command_args is None:
            return self._default_args_dict[quote_char]
        completion = create_args_snippet_from_command_args(command_args, quote_char,
                                                           for_json=False)

        return [sublime.CompletionItem(
            trigger="args",
            annotation="auto-detected",
            completion=completion,
            completion_format=sublime.COMPLETION_FORMAT_SNIPPET,
            kind=KIND_SNIPPET,
        )]
