import re

import sublime
import sublime_plugin

from sublime_lib.flags import RegionOption

from ..lib import syntax_paths

__all__ = (
    'SyntaxDefRegexCaptureGroupHighlighter',
)


class SyntaxDefRegexCaptureGroupHighlighter(sublime_plugin.ViewEventListener):

    @classmethod
    def applies_to_primary_view_only(cls):
        return False

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
            end = None
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
