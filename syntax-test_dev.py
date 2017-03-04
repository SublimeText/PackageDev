import sublime
import sublime_plugin
from os import path
import re
from collections import namedtuple


AssertionLineDetails = namedtuple(
    'AssertionLineDetails', ['comment_marker_match', 'assertion_colrange', 'line_region']
)
SyntaxTestHeader = namedtuple(
    'SyntaxTestHeader', ['comment_start', 'comment_end', 'syntax_file']
)


def get_syntax_test_tokens(view):
    """Parse the first line of the given view into a SyntaxTestHeader.

    Returns `None` if the file doesn't contain syntax tests.
    """

    line = view.line(0)
    match = None
    if line.size() < 1000:  # no point checking longer lines as they are unlikely to match
        first_line = view.substr(line)
        match = re.match(r'^(?P<comment_start>\s*\S+)'
                         r'\s+SYNTAX TEST\s+'
                         r'"(?P<syntax_file>[^"]+)"'
                         r'\s*(?P<comment_end>\S+)?$', first_line)
    if not match:
        return None
    else:
        return SyntaxTestHeader(**match.groupdict())


def is_syntax_test_file(view):
    """Determine if the given view is a syntax test file or not."""

    name = view.file_name()
    if not name:
        name = path.basename(name)
        return name.startswith('syntax_test_')
    else:
        header = get_syntax_test_tokens(view)
        return header and header.comment_start


def get_details_of_test_assertion_line(view, pos):
    """Parse details of a test assertion at a given position in a view.

    Always returns a AssertionLineDetails instance, whose fields may be `None`.
    """

    tokens = get_syntax_test_tokens(view) if is_syntax_test_file(view) else None
    if not tokens:
        return AssertionLineDetails(None, None, None)
    line_region = view.line(pos)
    line_text = view.substr(line_region)
    test_start_token = re.match(r'^\s*(' + re.escape(tokens.comment_start) + r')', line_text)
    assertion_colrange = None
    if test_start_token:
        assertion = re.match(r'\s*(?:(<-)|(\^+))', line_text[test_start_token.end():])
        if assertion:
            if assertion.group(1):
                assertion_colrange = (test_start_token.start(1),
                                      test_start_token.start(1))
            elif assertion.group(2):
                assertion_colrange = (test_start_token.end() + assertion.start(2),
                                      test_start_token.end() + assertion.end(2))

    return AssertionLineDetails(test_start_token, assertion_colrange, line_region)


def is_syntax_test_line(view, pos, must_contain_assertion):
    """Determine whether the line at the given character position is a syntax test line.

    It can optionally treat lines with comment markers but no assertion as a syntax test,
    useful for while the line is being written.
    """

    details = get_details_of_test_assertion_line(view, pos)
    if details.comment_marker_match:
        return not must_contain_assertion or details.assertion_colrange is not None
    return False


def get_details_of_line_being_tested(view):
    """Given a view, and starting from the cursor position, work upwards
    to find all syntax test lines that occur before the line that is being tested.
    Return a tuple containing a list of assertion line details,
    along with the region of the line being tested.
    """

    if not is_syntax_test_file(view):
        return (None, None)

    lines = []
    pos = view.sel()[0].begin()
    first_line = True
    while pos >= 0:
        details = get_details_of_test_assertion_line(view, pos)
        pos = details.line_region.begin() - 1
        if details.assertion_colrange:
            lines.append(details)
        elif not first_line or not details.comment_marker_match:
            break
        elif details.comment_marker_match:
            lines.append(details)
        first_line = False

    return (lines, details.line_region)


def find_common_scopes(scopes, skip_syntax_suffix):
    """Find the (partial) scopes that are common for a list of scopes.

    Example of unique scopes for the following Python code (and test positions):

    def function():
    ^^^^^^^^^^^^^^
    [
      'source.python meta.function.python storage.type.function.python',
      'source.python meta.function.python',
      'source.python meta.function.python entity.name.function.python',
      'source.python meta.function.parameters.python punctuation.section.parameters.begin.python'
    ]

    The common scope for these, ignoring the base scope, will be 'meta.function'
    """

    # we will use the scopes from index 0 and test against the scopes from the further indexes
    # as any scopes that doesn't appear in this index aren't worth checking, they can't be common

    # skip the base scope i.e. `source.python`
    check_scopes = scopes[0].split()[1:]

    shared_scopes = ''
    # stop as soon as at least one shared scope was found
    # or when there are no partial scopes left to check
    while not shared_scopes and check_scopes:
        if not skip_syntax_suffix:
            for check_scope in check_scopes:
                # check that the scope matches when combined with the shared scopes that have
                # already been discovered, because order matters (a space in a scope selector
                # is an operator, meaning the next scope must appear somewhere to the right
                # of the one before), and some scopes may appear more than once
                compare_with = shared_scopes + check_scope
                if all(sublime.score_selector(scope, compare_with) > 0 for scope in scopes):
                    shared_scopes += check_scope + ' '

        # if no matches were found
        if not shared_scopes:
            # split off the last partial scope from each scope to check
            # i.e. `meta.function.parameters` becomes `meta.function`
            # if the scope to check doesn't contain any sub-scopes i.e. `meta`,
            # then drop it from the list of scopes to check
            check_scopes = [
                '.'.join(check_scope.split('.')[0:-1])
                for check_scope in check_scopes if '.' in check_scope
            ]
            skip_syntax_suffix = False

    return shared_scopes.strip()


class AlignSyntaxTestCommand(sublime_plugin.TextCommand):

    """Align the cursor with spaces to be to the right of the previous line's assertion."""

    def run(self, edit):
        cursor = self.view.sel()[0]
        details = get_details_of_test_assertion_line(self.view, cursor.begin())
        if not details.comment_marker_match:
            return

        # find the last test assertion column on the previous line
        details = get_details_of_test_assertion_line(self.view, details.line_region.begin() - 1)
        next_col = None
        if not details.assertion_colrange:
            # the previous line wasn't a syntax test line, so instead
            # find the first non-whitespace char on the line being tested above
            for pos in range(details.line_region.begin(), details.line_region.end()):
                if self.view.substr(pos).strip() != '':
                    break
            next_col = self.view.rowcol(pos)[1]
        else:
            next_col = details.assertion_colrange[1]
        col_diff = next_col - self.view.rowcol(cursor.begin())[1]
        self.view.insert(edit, cursor.end(), " " * col_diff)
        self.view.run_command('suggest_syntax_test')


class SuggestSyntaxTestCommand(sublime_plugin.TextCommand):
    """Intelligently suggest where the syntax test assertions should be placed.

    This is based on the scopes of the line being tested, and where they change.
    """

    def run(self, edit, character='^'):
        """Available parameters:
        edit (sublime.Edit)
            The edit parameter from TextCommand.
        character (str) = '^'
            The character to insert when suggesting where the test assertions should go.
        """

        view = self.view
        view.replace(edit, view.sel()[0], character)
        insert_at = view.sel()[0].begin()
        if not is_syntax_test_file(view):
            return

        lines, line = get_details_of_line_being_tested(view)
        end_token = get_syntax_test_tokens(view).comment_end
        # don't duplicate the end token if it is on the line but not selected
        if end_token and view.sel()[0].end() == lines[0].line_region.end():
            end_token = ' ' + end_token
        else:
            end_token = ''

        scopes = []
        length = 0
        # find the following columns on the line to be tested where the scopes don't change
        test_at_start_of_comment = False
        col = view.rowcol(insert_at)[1]
        assertion_colrange = lines[0].assertion_colrange or (-1, -1)
        if assertion_colrange[0] == assertion_colrange[1]:
            col = assertion_colrange[1]
            test_at_start_of_comment = True
            lines = lines[1:]

        for pos in range(line.begin() + col, line.end() + 1):
            scope = view.scope_name(pos)
            if len(scopes) == 0:
                scopes.append(scope)
            elif scope != scopes[0]:
                break
            length += 1
            if test_at_start_of_comment:
                break

        # find the unique scopes at each existing assertion position
        if lines and not test_at_start_of_comment:
            col_start, col_end = lines[0].assertion_colrange
            for pos in range(line.begin() + col_start, line.begin() + col_end):
                scope = view.scope_name(pos)
                if scope not in scopes:
                    scopes.append(scope)

        prefs = sublime.load_settings('PackageDev.sublime-settings')
        suggest_suffix = prefs.get('syntax_test_suggest_scope_suffix', True)

        scope = find_common_scopes(scopes, not suggest_suffix)

        # delete the existing selection
        if not view.sel()[0].empty():
            view.erase(edit, view.sel()[0])

        view.insert(edit, insert_at, (character * length) + ' ' + scope + end_token)

        # move the selection to cover the added scope name,
        # so that the user can easily insert another ^ to extend the test
        view.sel().clear()
        view.sel().add(sublime.Region(
            insert_at + length,
            insert_at + length + len(' ' + scope + end_token)
        ))


class HighlightTestViewEventListener(sublime_plugin.ViewEventListener):
    def on_selection_modified_async(self):
        """Update highlighting of what the current line's test assertions point at."""

        if len(self.view.sel()) == 0:
            return
        cursor = self.view.sel()[0]
        highlight_only_cursor = False
        if cursor.empty():
            cursor = sublime.Region(cursor.begin(), cursor.end() + 1)
        else:
            highlight_only_cursor = re.match(r'^\^+$', self.view.substr(cursor)) is not None

        lines, line = get_details_of_line_being_tested(self.view)

        if not lines or not lines[0].assertion_colrange:
            self.view.erase_regions('current_syntax_test')
            return

        col_start, col_end = lines[0].assertion_colrange
        if highlight_only_cursor:
            col_start = self.view.rowcol(cursor.begin())[1]
            col_end = self.view.rowcol(cursor.end())[1]
        elif col_end == col_start:
            col_end += 1

        region = sublime.Region(line.begin() + col_start, line.begin() + col_end)

        prefs = sublime.load_settings('PackageDev.sublime-settings')
        scope = prefs.get('syntax_test_highlight_scope', 'text')
        styles = prefs.get('syntax_test_highlight_styles', ['DRAW_NO_FILL'])
        style_flags = 0
        # the following available add_region styles are taken from the API documentation:
        # http://www.sublimetext.com/docs/3/api_reference.html#sublime.View
        # unfortunately, the `sublime` module doesn't encapsulate them for easy reference
        # so we hardcode them here
        for style in styles:
            if style in [
                'DRAW_EMPTY', 'HIDE_ON_MINIMAP', 'DRAW_EMPTY_AS_OVERWRITE', 'DRAW_NO_FILL',
                'DRAW_NO_OUTLINE', 'DRAW_SOLID_UNDERLINE', 'DRAW_STIPPLED_UNDERLINE',
                'DRAW_SQUIGGLY_UNDERLINE', 'HIDDEN', 'PERSISTENT'
            ]:
                style_flags |= getattr(sublime, style)

        self.view.add_regions('current_syntax_test', [region], scope, '', style_flags)

    def on_query_context(self, key, operator, operand, match_all):
        """Respond to relevant syntax test keybinding contexts."""

        view = self.view
        # all contexts supported will have boolean results, so ignore regex operators
        if operator not in (sublime.OP_EQUAL, sublime.OP_NOT_EQUAL):
            return None

        def current_line_is_a_syntax_test():
            results = (is_syntax_test_line(view, reg.begin(), False)
                       for reg in view.sel())
            aggregator = all if match_all else any
            return aggregator(results)

        keys = {
            "current_line_is_a_syntax_test": current_line_is_a_syntax_test,
            "file_contains_syntax_tests": lambda: is_syntax_test_file(view),
        }

        if key not in keys:
            return None
        else:
            result = keys[key]() == bool(operand)
            if operator == sublime.OP_NOT_EQUAL:
                result = not result
            return result


class AssignSyntaxTestSyntaxListener(sublime_plugin.EventListener):

    """Assign target syntax highlighting to a syntax test file."""

    def on_load_async(self, view):
        test_header = get_syntax_test_tokens(view)
        if test_header and test_header.syntax_file:
            if view.settings().get('syntax', None) != test_header.syntax_file:
                view.assign_syntax(test_header.syntax_file)
