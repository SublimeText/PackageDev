import logging
import re
from collections import namedtuple

import sublime
import sublime_plugin

from ..lib.scope_data import (
    COMMIT_SCOPE_COMPLETION_CMD,
    COMPILED_HEADS,
    create_scope_suffix_completion
)
from ..lib import syntax_paths
from ..lib import inhibit_word_completions

__all__ = (
    'SyntaxDefCompletionsListener',
    'PackagedevCommitScopeCompletionCommand'
)

logger = logging.getLogger(__name__)

CompletionTemplate = namedtuple('CompletionTemplate', ['kind', 'format', 'suffix'])

Completion = namedtuple('Completion', ['trigger', 'template', 'details'])

# a list of kinds used to denote the different kinds of completions
TPL_HEADER_BASE = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_TEXT,
    kind=(sublime.KIND_ID_NAMESPACE, 'K', 'Header Key'),
    suffix=": ",
)
TPL_HEADER_TRUE = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_NAMESPACE, 'K', 'Header Key'),
    suffix=": ${1:true}",
)
TPL_HEADER_DICT = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_NAMESPACE, 'D', 'Header Dict'),
    suffix=":\n  ",
)
TPL_HEADER_LIST = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_NAMESPACE, 'L', 'Header List'),
    suffix=":\n  - ",
)
TPL_BRANCH = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_NAVIGATION, 'b', 'Branch Point'),
    suffix=": ",
)
TPL_CONTEXT = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_KEYWORD, 'c', 'Context'),
    suffix=":\n  ",
)
TPL_FUNCTION = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_FUNCTION, 'f', 'Function'),
    suffix=": ",
)
TPL_FUNCTION_TRUE = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_FUNCTION, 'f', 'Function'),
    suffix=": ${1:true}",
)
TPL_FUNCTION_FALSE = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_FUNCTION, 'f', 'Function'),
    suffix=": ${1:false}",
)
TPL_FUNCTION_NUMERIC = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_FUNCTION, 'f', 'Function'),
    suffix=": ${1:1}",
)
TPL_CAPTURUES = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_FUNCTION, 'c', 'Captures'),
    suffix=":\n  ",
)
TPL_VARIABLE = CompletionTemplate(
    format=sublime.COMPLETION_FORMAT_SNIPPET,
    kind=(sublime.KIND_ID_VARIABLE, 'v', 'Variable'),
    suffix=": ",
)

PACKAGE_NAME = __package__.split('.')[0]


def status(msg, window=None, console=False):
    msg = "[%s] %s" % (PACKAGE_NAME, msg)
    (window or sublime).status_message(msg)
    if console:
        print(msg)


def format_static_completion(completion):
    return sublime.CompletionItem(
        trigger=completion.trigger,
        kind=completion.template.kind,
        details=completion.details,
        completion=completion.trigger + completion.template.suffix,
        completion_format=completion.template.format,
    )


def format_static_completions(templates):
    return list(map(format_static_completion, templates))


def format_completions(items, annotation="", kind=sublime.KIND_AMBIGUOUS):
    format_string = "Defined at line <a href='subl:goto_line {{\"line\": \"{0}\"}}'>{0}</a>"
    return [
        sublime.CompletionItem(
            trigger=trigger,
            annotation=annotation,
            kind=kind,
            details=format_string.format(row) if row is not None else "",
        )
        for trigger, row in items
    ]


class SyntaxDefCompletionsListener(sublime_plugin.ViewEventListener):

    base_completions_root = format_static_completions([
        # base keys
        Completion('name', TPL_HEADER_BASE, "The display name of the syntax."),
        Completion('scope', TPL_HEADER_BASE, "The main scope of the syntax."),
        Completion('version', TPL_HEADER_BASE, "The sublime-syntax version."),
        Completion('extends', TPL_HEADER_BASE, "The syntax which is to be extended."),
        Completion('name', TPL_HEADER_BASE, "The display name of the syntax."),
        Completion(
            "first_line_match",
            TPL_HEADER_BASE,
            "The pattern to identify a file by content.",
        ),

        Completion('hidden', TPL_HEADER_TRUE, "Hide this syntax from the menu."),
        # dict keys
        Completion('variables', TPL_HEADER_DICT, 'The variables definitions.'),
        Completion('contexts', TPL_HEADER_DICT, 'The syntax contexts.'),
        # list keys
        Completion('file_extensions', TPL_HEADER_LIST, "The list of file extensions."),
        Completion(
            'hidden_file_extensions',
            TPL_HEADER_LIST,
            "The list of hidden file extensions.",
        ),
    ])

    base_completions_contexts = format_static_completions([
        # meta functions
        Completion(
            'meta_append',
            TPL_FUNCTION_TRUE,
            "Add rules to the end of the inherit context.",
        ),
        Completion(
            'meta_content_scope',
            TPL_FUNCTION,
            "A scope to apply to the content of a context.",
        ),
        Completion(
            'meta_include_prototype',
            TPL_FUNCTION_FALSE,
            "Flag to in-/exclude `prototype`",
        ),
        Completion(
            'meta_prepend',
            TPL_FUNCTION_TRUE,
            "Add rules to the beginning of the inherit context.",
        ),
        Completion('meta_scope', TPL_FUNCTION, "A scope to apply to the full context."),
        Completion('clear_scopes', TPL_FUNCTION, "Clear meta scopes."),
        # matching tokens
        Completion('match', TPL_FUNCTION, "Pattern to match tokens."),
        # scoping
        Completion('scope', TPL_FUNCTION, "The scope to apply if a token matches"),
        Completion('captures', TPL_CAPTURUES, "Assigns scopes to the capture groups."),
        # contexts
        Completion('push', TPL_FUNCTION, "Push a context onto the stack."),
        Completion('set', TPL_FUNCTION, "Set a context onto the stack."),
        Completion('with_prototype', TPL_FUNCTION, "Rules to prepend to each context."),
        # branching
        Completion(
            'branch_point',
            TPL_FUNCTION,
            "Name of the point to rewind to if a branch fails.",
        ),
        Completion('branch', TPL_FUNCTION, "Push branches onto the stack."),
        Completion('fail', TPL_FUNCTION, "Fail the current branch."),
        # embedding
        Completion('embed', TPL_FUNCTION, "A context or syntax to embed."),
        Completion('embed_scope', TPL_FUNCTION, "A scope to apply to the embedded syntax."),
        Completion('escape', TPL_FUNCTION, "A pattern to denote the end of the embedded syntax."),
        Completion('escape_captures', TPL_CAPTURUES, "Assigns scopes to the capture groups."),
        # including
        Completion('include', TPL_FUNCTION, "Includes a context."),
        Completion('apply_prototype', TPL_FUNCTION_TRUE, "Apply prototype of included syntax."),
    ])

    base_completions_contexts_version_1 = (
        base_completions_contexts
        + format_static_completions([
            Completion('pop', TPL_FUNCTION_TRUE, 'Pop context(s) from the stack.'),
        ])
    )

    base_completions_contexts_version_2 = (
        base_completions_contexts
        + format_static_completions([
            Completion('pop', TPL_FUNCTION_NUMERIC, 'Pop context(s) from the stack.'),
        ])
    )

    @classmethod
    def applies_to_primary_view_only(cls):
        return False

    @classmethod
    def is_applicable(cls, settings):
        return settings.get('syntax') == syntax_paths.SYNTAX_DEF

    @inhibit_word_completions
    def on_query_completions(self, prefix, locations):

        def match_selector(selector, offset=0):
            """Verify scope for each location."""
            return all(self.view.match_selector(point + offset, selector)
                       for point in locations)

        # None of our business
        if not match_selector("- comment - (source.regexp - keyword.other.variable)"):
            return None

        # Scope name completions based on our scope_data database
        if match_selector("meta.expect-scope, meta.scope", -1):
            return self._complete_scope(prefix, locations)

        # Auto-completion for include values using the 'contexts' keys and for
        if match_selector(
            "meta.expect-context-list-or-content | meta.context-list-or-content",
            -1,
        ):
            return ((self._complete_keyword(prefix, locations) or [])
                    + self._complete_context(prefix, locations))

        # Auto-completion for include values using the 'contexts' keys
        if match_selector(
            "meta.expect-context-list | meta.expect-context | meta.include | meta.context-list",
            -1,
        ):
            return self._complete_context(prefix, locations) or None

        # Auto-completion for branch points with 'fail' key
        if match_selector(
            "meta.expect-branch-point-reference | meta.branch-point-reference",
            -1,
        ):
            return self._complete_branch_point()

        # Auto-completion for variables in match patterns using 'variables' keys
        if match_selector("keyword.other.variable"):
            return self._complete_variable()

        # Standard completions for unmatched regions
        return self._complete_keyword(prefix, locations)

    def _line_prefix(self, point):
        _, col = self.view.rowcol(point)
        line = self.view.substr(self.view.line(point))
        return line[:col]

    def _complete_context(self, prefix, locations):
        # Verify that we're not looking for an external include
        for point in locations:
            line_prefix = self._line_prefix(point)
            real_prefix = re.search(r"[^,\[ ]*$", line_prefix).group(0)
            if real_prefix.startswith("scope:") or "/" in real_prefix:
                return []  # Don't show any completions here
            elif real_prefix != prefix:
                # print("Unexpected prefix mismatch: {} vs {}".format(real_prefix, prefix))
                return []

        return format_completions(
            [(self.view.substr(r), self.view.rowcol(r.begin())[0] + 1)
             for r in self.view.find_by_selector("entity.name.function.context")],
            annotation="",
            kind=TPL_CONTEXT.kind,
        )

    def _complete_keyword(self, prefix, locations):

        def match_selector(selector, offset=0):
            """Verify scope for each location."""
            return all(self.view.match_selector(point + offset, selector)
                       for point in locations)

        prefixes = set()
        for point in locations:
            # Ensure that we are completing a key name everywhere
            line_prefix = self._line_prefix(point)
            real_prefix = re.sub(r"^ +(- +)*", " ", line_prefix)  # collapse leading whitespace
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
        elif match_selector("meta.block.contexts"):
            if self._determine_version() == 1:
                return self.base_completions_contexts_version_1
            else:
                return self.base_completions_contexts_version_2
        else:
            return None

    def _complete_scope(self, prefix, locations):
        # Determine entire prefix
        window = self.view.window()
        prefixes = set()
        for point in locations:
            *_, real_prefix = self._line_prefix(point).rpartition(" ")
            prefixes.add(real_prefix)

        if len(prefixes) > 1:
            return None
        else:
            real_prefix = next(iter(prefixes))

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
                status(
                    "`%s` not found in scope naming conventions" % '.'.join(tokens[:i + 1]),
                    window
                )
                break
            nodes = node.children
            if not nodes:
                status("No nodes available in scope naming conventions after `%s`"
                       % '.'.join(tokens[:-1]), window)
                break
        else:
            # Offer to complete from conventions or base scope
            return nodes.to_completion() + base_scope_completion

        # Since we don't have anything to offer,
        # just complete the base scope appendix/suffix.
        return base_scope_completion

    def _complete_base_scope(self, last_token):
        regions = self.view.find_by_selector("meta.scope string - meta.block")
        if len(regions) != 1:
            status(
                "Warning: Could not determine base scope uniquely",
                console=True
            )
            return []

        # TODO some syntaxes use a different suffix than the last segment of the base scope
        base_scope = self.view.substr(regions[0])
        *_, base_suffix = base_scope.rpartition(".")
        # Only useful when the base scope suffix is not already the last one
        # In this case it is even useful to inhibit other completions completely
        if last_token == base_suffix:
            return []

        return [create_scope_suffix_completion(base_suffix)]

    def _complete_variable(self):
        return format_completions(
            [(self.view.substr(r), self.view.rowcol(r.begin())[0] + 1)
             for r in self.view.find_by_selector("entity.name.constant")],
            annotation="",
            kind=TPL_VARIABLE.kind,
        )

    def _complete_branch_point(self):
        return format_completions(
            [(self.view.substr(r), self.view.rowcol(r.begin())[0] + 1)
             for r in self.view.find_by_selector("entity.name.label.branch-point")],
            annotation="",
            kind=TPL_BRANCH.kind,
        )

    def _determine_version(self):
        version_regions = self.view.find_by_selector('storage.type.version.sublime-syntax')
        if version_regions:
            if len(version_regions) > 1:
                logger.debug("Found multiple versions (%d), using last", len(version_regions))
            version_line = self.view.substr(self.view.line(version_regions[-1]))
            *_, version_str = version_line.partition(": ")
            if version_str:
                try:
                    return int(version_str)
                except ValueError:
                    logger.debug("Unable to parse version string '%s'", version_str)
        return 1


class PackagedevCommitScopeCompletionCommand(sublime_plugin.TextCommand):

    """Insert a scope segment and re-open the completions popup when sensible."""

    def name(self):
        return COMMIT_SCOPE_COMPLETION_CMD

    def run(self, edit, text, is_base_suffix=False):
        self.view.run_command("insert", {"characters": text})

        if is_base_suffix:
            return

        self.view.run_command('insert', {'characters': "."})

        # Allow ST to process our inserts (and work around a crash).
        sublime.set_timeout(
            lambda: self.view.run_command('auto_complete', {'disable_auto_insert': True}),
        )
