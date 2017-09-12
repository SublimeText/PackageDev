import functools
import itertools
import re

import sublime
import sublime_plugin

from .lib.sublime_lib.constants import style_flags_from_list
from .lib.scope_data import COMPILED_HEADS

__all__ = (
    'SyntaxDefRegexCaptureGroupHighlighter',
    'SyntaxDefCompletionsListener',
    'PostCompletionsListener',
)

PACKAGE_NAME = __package__.split('.')[0]

SYNTAX_DEF_FILENAME = ("Sublime Text Syntax Definition.sublime-syntax")
SYNTAX_DEF_PATH = (
    "Packages/{}/Package/Sublime Text Syntax Definition/{}"
    .format(PACKAGE_NAME, SYNTAX_DEF_FILENAME)
)


def status(msg, console=False):
    msg = "[%s] %s" % (PACKAGE_NAME, msg)
    sublime.status_message(msg)
    if console:
        print(msg)


class SyntaxDefRegexCaptureGroupHighlighter(sublime_plugin.ViewEventListener):

    @classmethod
    def is_applicable(cls, settings):
        return settings.get('syntax') == SYNTAX_DEF_PATH

    def on_selection_modified(self):
        prefs = sublime.load_settings('PackageDev.sublime-settings')
        scope = prefs.get('syntax_captures_highlight_scope', 'text')
        styles = prefs.get('syntax_captures_highlight_styles', ['DRAW_NO_FILL'])

        style_flags = style_flags_from_list(styles)

        self.view.add_regions(
            key='captures',
            regions=list(self.get_regex_regions()),
            scope=scope,
            flags=style_flags,
        )

    def get_regex_regions(self):
        locations = [
            region.begin()
            for selection in self.view.sel()
            if self.view.match_selector(
                selection.begin(),
                'source.yaml.sublime.syntax meta.expect-captures.yaml'
            )
            for region in self.view.split_by_newlines(selection)
        ]

        for loc in locations:
            # Find the line number.
            match = re.search(r'(\d+):', self.view.substr(self.view.line(loc)))
            if not match:
                continue
            n = int(match.group(1))

            # Find the associated regexp. Assume it's the preceding one.
            try:
                regexp_region = [
                    region
                    for region in self.view.find_by_selector('source.regexp.oniguruma')
                    if region.end() < loc
                ][-1]
            except IndexError:
                continue

            if n == 0:
                yield regexp_region
                continue

            # Find parens that define capture groups.
            regexp_offset = regexp_region.begin()
            parens = iter(
                (match.group(), match.start() + regexp_offset)
                for match in re.finditer(r'\(\??|\)', self.view.substr(regexp_region))
                if self.view.match_selector(
                    match.start() + regexp_offset,
                    'keyword.control.group'
                )
            )

            # Find the start of the nth capture group.
            start = None
            count = 0
            for p, i in parens:
                if p == '(':  # Not (?
                    count += 1
                    if count == n:
                        start = i
                        break

            # Find the end of that capture group
            end   = None
            depth = 0
            for p, i in parens:
                if p in {'(', '(?'}:
                    depth += 1
                else:
                    if depth == 0:
                        end = i + 1
                        break
                    else:
                        depth -= 1

            if end is not None:
                yield sublime.Region(start, end)


def _inhibit_word_completions(func):
    """Decorator that inhibits ST's word completions if non-None value is returned."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        if ret is not None:
            return (ret, sublime.INHIBIT_WORD_COMPLETIONS)

    return wrapper


def _build_completions(base_keys=(), dict_keys=(), list_keys=()):
    generator = itertools.chain(
        (("{0}\t{0}:".format(s), "%s: "    % s) for s in base_keys),
        (("{0}\t{0}:".format(s), "%s:\n  " % s) for s in dict_keys),
        (("{0}\t{0}:".format(s), "%s:\n- " % s) for s in list_keys)
    )
    return tuple(sorted(generator))


class SyntaxDefCompletionsListener(sublime_plugin.ViewEventListener):

    base_completions_root = _build_completions(
        base_keys=('scope', 'name'),
        dict_keys=('variables', 'contexts'),
        list_keys=('file_extensions',),
    )

    base_completions_contexts = _build_completions(
        base_keys=('scope', 'match', 'include', 'push', 'with_prototype',  # 'pop',
                   'meta_scope', 'meta_content_scope', 'meta_include_prototype', 'clear_scopes'),
        dict_keys=('captures',),
    )
    base_completions_contexts += (("pop\tpop: true", "pop: true"),)

    # These instance variables are for communicating
    # with our PostCompletionsListener instance.
    is_completing_scope = False
    base_suffix = None

    @classmethod
    def is_applicable(cls, settings):
        return settings.get('syntax') == SYNTAX_DEF_PATH

    def _line_prefix(self, point):
        _, col = self.view.rowcol(point)
        line = self.view.substr(self.view.line(point))
        return line[:col]

    def _complete_base_scope(self, last_token):
        regions = self.view.find_by_selector("meta.scope string - meta.block")
        if len(regions) != 1:
            status("Warning: Could not determine base scope uniquely", console=True)
            self.base_suffix = None
            return []

        base_scope = self.view.substr(regions[0])
        *_, base_suffix = base_scope.rpartition(".")
        # Only useful when the base scope suffix is not already the last one
        # In this case it is even useful to inhibit other completions completely
        if last_token == base_suffix:
            self.base_suffix = None
            return []

        self.base_suffix = base_suffix

        return [(base_suffix + "\tbase suffix", base_suffix)]

    @_inhibit_word_completions
    def on_query_completions(self, prefix, locations):

        def verify_scope(selector, offset=0):
            """Verify scope for each location."""
            return all(self.view.match_selector(point + offset, selector)
                       for point in locations)

        # None of our business
        if not verify_scope("- comment - (source.regexp - keyword.other.variable)"):
            return None

        # Scope name completions based on our scope_data database
        elif verify_scope("meta.expect-scope, meta.scope", -1):

            # Determine entire prefix
            prefixes = set()
            for point in locations:
                *_, real_prefix = self._line_prefix(point).rpartition(" ")
                prefixes.add(real_prefix)

            if len(prefixes) > 1:
                return None
            else:
                real_prefix = next(iter(prefixes))

            # We're not leaving this block anymore now
            self.is_completing_scope = True

            # Tokenize the current selector
            tokens = real_prefix.split(".")
            if len(tokens) <= 1:
                # No work to be done here, just return the heads
                return COMPILED_HEADS.to_completion()

            base_scope_completion = self._complete_base_scope(tokens[-1])
            # Browse the nodes and their children
            nodes = COMPILED_HEADS
            for i, token in enumerate(tokens[:-1]):
                node = nodes.find(token)
                if not node:
                    status("`%s` not found in scope naming conventions" % '.'.join(tokens[:i + 1]))
                    break
                nodes = node.children
                if not nodes:
                    status("No nodes available in scope naming conventions after `%s`"
                           % '.'.join(tokens[:-1]))
                    break
            else:
                # Offer to complete from conventions or base scope
                return nodes.to_completion() + base_scope_completion

            # Since we don't have anything to offer,
            # just complete the base scope appendix/suffix.
            return base_scope_completion

        # Auto-completion for include values using the 'contexts' keys
        elif verify_scope("meta.expect-include-list | meta.expect-include"
                          " | meta.include | meta.include-list"):
            # Verify that we're not looking for an external include
            for point in locations:
                line_prefix = self._line_prefix(point)
                real_prefix = re.search(r"[^,\[ ]*$", line_prefix).group(0)
                if real_prefix.startswith("scope:") or "/" in real_prefix:
                    return []  # Don't show any completions here
                elif real_prefix != prefix:
                    # print("Unexpected prefix mismatch: {} vs {}".format(real_prefix, prefix))
                    return []

            context_names = [self.view.substr(r)
                             for r in self.view.find_by_selector("entity.name.context")]

            return [(ctx + "\tcontext", ctx) for ctx in context_names]

        # Auto-completion for variables in match patterns using 'variables' keys
        elif verify_scope("keyword.other.variable"):
            variable_names = [self.view.substr(r)
                              for r in self.view.find_by_selector("entity.name.constant")]

            return [(var + "\tvariable", var) for var in variable_names]

        # Standard completions for unmatched regions
        else:
            prefixes = set()
            for point in locations:
                # Ensure that we are completing a key name everywhere
                line_prefix = self._line_prefix(point)
                real_prefix = re.sub(r"^ +(- +)?", " ", line_prefix)  # collapse leading whitespace
                prefixes.add(real_prefix)

            if len(prefixes) != 1:
                return None
            else:
                real_prefix = next(iter(prefixes))

            # (Supposedly) all keys start their own line
            match = re.match(r"^(\s*)[\w-]*$", real_prefix)
            if not match:
                return None
            elif not match.group(1):
                return self.base_completions_root
            elif verify_scope("meta.block.contexts"):
                return self.base_completions_contexts
            else:
                return None


class PostCompletionsListener(sublime_plugin.EventListener):

    """Insert a dot and re-open the completions popup when completing a scope segment.

    A separate class is needed
    because on_post_text_command is not available to ViewEventListeners.
    """

    def on_post_text_command(self, view, command_name, args):
        if command_name == 'hide_auto_complete':
            listener = sublime_plugin.find_view_event_listener(view, SyntaxDefCompletionsListener)
            if listener:
                listener.is_completing_scope = False
        if command_name in ('commit_completion', 'insert_best_completion'):
            listener = sublime_plugin.find_view_event_listener(view, SyntaxDefCompletionsListener)
            if not (listener and listener.is_completing_scope):
                return

            listener.is_completing_scope = False

            point = view.sel()[0].a

            # Check if the completed value was the base suffix
            # and don't re-open auto complete in that case.
            if listener.base_suffix:
                region = sublime.Region(point - len(listener.base_suffix) - 1, point)
                if view.substr(region) == "." + listener.base_suffix:
                    return

            # Chck if completions were requested within a scope name.
            if view.substr(point) == ".":
                return

            view.run_command('insert', {'characters': "."})
            view.run_command('auto_complete', {'disable_auto_insert': True})
