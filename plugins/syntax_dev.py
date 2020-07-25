import functools
import re

import sublime
import sublime_plugin

from sublime_lib.flags import RegionOption

from .lib.scope_data import COMPILED_HEADS
from .lib import syntax_paths

__all__ = (
    'SyntaxDefRegexCaptureGroupHighlighter',
    'SyntaxDefCompletionsListener',
    'PackagedevCommitScopeCompletionCommand'
)

PACKAGE_NAME = __package__.split('.')[0]


def status(msg, console=False):
    msg = "[%s] %s" % (PACKAGE_NAME, msg)
    sublime.status_message(msg)
    if console:
        print(msg)


class SyntaxDefRegexCaptureGroupHighlighter(sublime_plugin.ViewEventListener):

    # TODO multiple views into the same file

    @classmethod
    def is_applicable(cls, settings):
        return settings.get('syntax') == syntax_paths.SYNTAX_DEF

    def on_selection_modified(self):
        prefs = sublime.load_settings('PackageDev.sublime-settings')
        scope = prefs.get('syntax.captures_highlight_scope', "text")
        styles = prefs.get('syntax.captures_highlight_styles', ['DRAW_NO_FILL'])

        style_flags = RegionOption(*styles)

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
                'source.yaml.sublime.syntax meta.expect-captures'
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
        return (ret, sublime.INHIBIT_WORD_COMPLETIONS) if ret else ret

    return wrapper


HAVE_KINDS = hasattr(sublime, 'CompletionItem')
if HAVE_KINDS:

    # a list of kinds used to denote the different kinds of completions
    KIND_HEADER_BASE = (sublime.KIND_ID_NAMESPACE, 'K', 'Header Key')
    KIND_HEADER_DICT = (sublime.KIND_ID_NAMESPACE, 'D', 'Header Dict')
    KIND_HEADER_LIST = (sublime.KIND_ID_NAMESPACE, 'L', 'Header List')
    KIND_BRANCH = (sublime.KIND_ID_NAVIGATION, 'b', 'Branch Point')
    KIND_CONTEXT = (sublime.KIND_ID_KEYWORD, 'c', 'Context')
    KIND_FUNCTION = (sublime.KIND_ID_FUNCTION, 'f', 'Function')
    KIND_CAPTURUE = (sublime.KIND_ID_FUNCTION, 'c', 'Captures')
    KIND_SCOPE = (sublime.KIND_ID_NAMESPACE, 's', 'Scope')
    KIND_VARIABLE = (sublime.KIND_ID_VARIABLE, 'v', 'Variable')

    def format_static_completions(templates):

        def format_item(trigger, kind, details):
            if kind in (KIND_HEADER_DICT, KIND_CAPTURUE, KIND_CONTEXT):
                completion_format = sublime.COMPLETION_FORMAT_SNIPPET
                suffix = ":\n  "
            elif kind is KIND_HEADER_LIST:
                completion_format = sublime.COMPLETION_FORMAT_SNIPPET
                suffix = ":\n  - "
            else:
                completion_format = sublime.COMPLETION_FORMAT_TEXT
                suffix = ": "

            return sublime.CompletionItem(
                trigger=trigger, kind=kind, details=details,
                completion=trigger + suffix, completion_format=completion_format
            )

        return [format_item(*template) for template in templates]

    def format_completions(items, annotation="", kind=sublime.KIND_AMBIGUOUS):
        format_string = "Defined at line <a href='subl:goto_line {{\"line\": \"{0}\"}}'>{0}</a>"
        return [
            sublime.CompletionItem(
                trigger=trigger, annotation=annotation, kind=kind,
                details=format_string.format(row) if row is not None else ""
            )
            for trigger, row in items
        ]

    def format_branch_completions(items):
        return format_completions(items, "", KIND_BRANCH)

    def format_context_completions(items):
        return format_completions(items, "", KIND_CONTEXT)

    def format_base_completion(item):
        return format_completions([[item, None], ], "base suffix", KIND_SCOPE)

    def format_scope_completions(items):
        return format_completions(items, "convention", KIND_SCOPE)

    def format_variable_completions(items):
        return format_completions(items, "", KIND_VARIABLE)

else:

    KIND_HEADER_BASE = ''
    KIND_HEADER_DICT = ''
    KIND_HEADER_LIST = ''
    KIND_BRANCH = ''
    KIND_CONTEXT = ''
    KIND_FUNCTION = ''
    KIND_CAPTURUE = ''
    KIND_VARIABLE = ''

    def format_static_completions(templates):

        def format_item(trigger, kind, details):
            if kind in (KIND_HEADER_DICT, KIND_CAPTURUE, KIND_CONTEXT):
                suffix = ":\n  "
            elif kind is KIND_HEADER_LIST:
                suffix = ":\n  - "
            else:
                suffix = ": "

            return ("{0}\t{1}".format(trigger, details), trigger + suffix)

        return [format_item(*template) for template in templates]

    def format_completions(items, kind):
        return [trigger + kind for trigger, _ in items]

    def format_base_completion(item):
        return [item + "\tbase suffix"]

    def format_branch_completions(items):
        return format_completions(items, "\tbranch point")

    def format_context_completions(items):
        return format_completions(items, "\tcontext")

    def format_scope_completions(items):
        return format_completions(items, "\tconvention")

    def format_variable_completions(items):
        return format_completions(items, "\tvariable")


class SyntaxDefCompletionsListener(sublime_plugin.ViewEventListener):

    base_completions_root = format_static_completions(templates=(
        # base keys
        ('name', KIND_HEADER_BASE, 'The display name of the syntax.'),
        ('scope', KIND_HEADER_BASE, 'The main scope of the syntax.'),
        ('version', KIND_HEADER_BASE, 'The sublime-syntax version.'),
        ('extends', KIND_HEADER_BASE, 'The syntax which is to be extended.'),
        ('name', KIND_HEADER_BASE, 'The display name of the syntax.'),
        ('first_line_match', KIND_HEADER_BASE, 'The pattern to identify a file by content.'),
        # dict keys
        ('variables', KIND_HEADER_DICT, 'The variables definitions.'),
        ('contexts', KIND_HEADER_DICT, 'The syntax contexts.'),
        # list keys
        ('file_extensions', KIND_HEADER_LIST, 'The list of file extensions.'),
        ('hidden_extensions', KIND_HEADER_LIST, 'The list of hidden file extensions.')
    ))

    base_completions_contexts = format_static_completions(templates=(
        # meta functions
        ('meta_append', KIND_FUNCTION, 'Add rules to the end of the inherit context.'),
        ('meta_content_scope', KIND_FUNCTION, 'A scope to apply to the content of a context.'),
        ('meta_include_prototype', KIND_FUNCTION, 'Flag to include/exclude `prototype`'),
        ('meta_prepend', KIND_FUNCTION, 'Add rules to the beginning of the inherit context.'),
        ('meta_scope', KIND_FUNCTION, 'A scope to apply to the full context.'),
        ('clear_scopes', KIND_FUNCTION, 'Clear meta scopes.'),
        # matching tokens
        ('match', KIND_FUNCTION, 'Pattern to match tokens.'),
        # scoping
        ('scope', KIND_FUNCTION, 'The scope to apply if a token matches'),
        ('captures', KIND_CAPTURUE, 'Assigns scopes to the capture groups.'),
        # contexts
        ('push', KIND_FUNCTION, 'Push a context onto the stack.'),
        ('set', KIND_FUNCTION, 'Set a context onto the stack.'),
        ('with_prototype', KIND_FUNCTION, 'Rules to prepend to each context.'),
        # branching
        ('branch_point', KIND_FUNCTION, 'Name of the point to rewind to if a branch fails.'),
        ('branch', KIND_FUNCTION, 'Push branches onto the stack.'),
        ('fail', KIND_FUNCTION, 'Fail the current branch.'),
        # embedding
        ('embed', KIND_FUNCTION, 'A context or syntax to embed.'),
        ('embed_scope', KIND_FUNCTION, 'A scope to apply to the embedded syntax.'),
        ('escape', KIND_FUNCTION, 'A pattern to denote the end of the embedded syntax.'),
        ('escape_captures', KIND_CAPTURUE, 'Assigns scopes to the capture groups.'),
        # including
        ('include', KIND_FUNCTION, 'Includes a context.'),
        ('apply_prototype', KIND_FUNCTION, 'If `true` apply prototype of included syntax.'),
    ))

    base_completions_contexts += (("pop\tpop: true", "pop: ${1:true}"),)

    # These instance variables are for communicating
    # with our PostCompletionsListener instance.
    base_suffix = None

    @classmethod
    def applies_to_primary_view_only(cls):
        return False

    @classmethod
    def is_applicable(cls, settings):
        return settings.get('syntax') == syntax_paths.SYNTAX_DEF

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
        if verify_scope("meta.expect-scope, meta.scope", -1):
            return self._complete_scope(prefix, locations)

        # Auto-completion for include values using the 'contexts' keys and for
        if verify_scope("meta.expect-context-list-or-content"
                        " | meta.context-list-or-content", -1):
            return self._complete_keyword(prefix, locations) + \
                self._complete_context(prefix, locations)

        # Auto-completion for include values using the 'contexts' keys
        if verify_scope("meta.expect-context-list | meta.expect-context"
                        " | meta.include | meta.context-list", -1):
            return self._complete_context(prefix, locations)

        # Auto-completion for branch points with 'fail' key
        if verify_scope("meta.expect-branch-point-reference"
                        " | meta.branch-point-reference", -1):
            return self._complete_branch_point()

        # Auto-completion for variables in match patterns using 'variables' keys
        if verify_scope("keyword.other.variable"):
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

        return format_context_completions(
            [
                self.view.substr(r),
                self.view.rowcol(r.begin())[0] + 1
            ]
            for r in self.view.find_by_selector("entity.name.function.context")
        )

    def _complete_keyword(self, prefix, locations):

        def verify_scope(selector, offset=0):
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
        elif verify_scope("meta.block.contexts"):
            return self.base_completions_contexts
        else:
            return None

    def _complete_scope(self, prefix, locations):
        # Determine entire prefix
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

        return format_base_completion(base_suffix)

    def _complete_variable(self):
        return format_variable_completions(
            [
                self.view.substr(r),
                self.view.rowcol(r.begin())[0] + 1
            ]
            for r in self.view.find_by_selector("entity.name.constant")
        )

    def _complete_branch_point(self):
        return format_branch_completions(
            [
                self.view.substr(r),
                self.view.rowcol(r.begin())[0] + 1
            ]
            for r in self.view.find_by_selector("entity.name.label.branch-point")
        )


class PackagedevCommitScopeCompletionCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.view.run_command("commit_completion")

        # Don't add duplicated dot, if scope is edited in the middle.
        if self.view.substr(self.view.sel()[0].a) == ".":
            return

        # Check if the completed value was the base suffix
        # and don't re-open auto complete in that case.
        listener = sublime_plugin.find_view_event_listener(self.view, SyntaxDefCompletionsListener)
        if listener and listener.base_suffix:
            point = self.view.sel()[0].a
            region = sublime.Region(point - len(listener.base_suffix) - 1, point)
            if self.view.substr(region) == "." + listener.base_suffix:
                return

        # Insert a . and trigger next completion
        self.view.run_command('insert', {'characters': "."})
        self.view.run_command('auto_complete', {'disable_auto_insert': True})
