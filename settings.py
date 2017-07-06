# -*- encoding: utf-8 -*-
import os
import re
import textwrap

import sublime
import sublime_plugin

POPUP_TEMPLATE = """
<body id="sublime-settings">
<style>
    body {{
        margin: 0;
        padding: 0;
    }}
    h1, h2 {{
        border-bottom: 1px solid color(var(--background) blend(white 80%));
        font-weight: normal;
        margin: 0;
        padding: 0.5rem;
    }}
    h1 {{
        color: color(var(--background) blend(var(--orangish) 20%));
        font-size: 1.0rem;
    }}
    h2 {{
        color: color(var(--background) blend(var(--foreground) 30%));
        font-size: 1.0rem;
        font-family: monospace;
    }}
    p {{
        margin: 0;
        padding: 0.5rem;
    }}
    a {{
        text-decoration: none;
    }}
</style>
{0}
</body>
"""

# match top-level keys only
KEY_SCOPE = 'keyword.other.name.key.sublime.settings'
VALUE_SCOPE = 'meta.structure.dictionary.value'


def html_encode(string):
    """Encode some critical characters to html entities."""
    return string.replace('&', '&amp;')           \
                 .replace('<', '&lt;')            \
                 .replace('>', '&gt;')            \
                 .replace('\t', '&nbsp;&nbsp;')   \
                 .replace('    ', '&nbsp;&nbsp;') \
                 .replace('\n', '<br>') if string else ''


def key_region(view, point):
    """Return the key region if point is on a settings key or None."""
    if view.match_selector(point, KEY_SCOPE):
        for region in view.find_by_selector(KEY_SCOPE):
            if region.contains(point):
                return region
    return None


def key_name(view, point):
    """Return the key name if point is on a settings key or None."""
    region = key_region(view, point)
    return view.substr(region).strip('"') if region else None


def value_region(view, point):
    """Return the value region if point is on a settings value or None."""
    if view.match_selector(point, VALUE_SCOPE):
        for region in view.find_by_selector(VALUE_SCOPE):
            if region.contains(point):
                return region
    return None


class SettingsListener(sublime_plugin.ViewEventListener):

    @classmethod
    def is_applicable(cls, settings):
        """Enable the listener for Sublime Settings syntax only."""
        # view is member of side-by-side settings
        result = settings.get('edit_settings_view') in ('base', 'user')
        if not result:
            syntax = settings.get('syntax') or ''
            result = syntax.endswith('/Sublime Text Settings.sublime-syntax')
        return result

    def __init__(self, view):
        """Initialize view event listener object."""
        super(SettingsListener, self).__init__(view)
        try:
            # try to attach to known settings object.
            self.known_settings = KnownSettings(view.file_name())
            # need to wait a little bit for the view to become valid
            sublime.set_timeout_async(self.do_linting, 200)
        except ValueError:
            self.known_settings = None

    def on_modified(self):
        """Sublime Text modified event handler to update linting."""
        self.do_linting()

    def on_query_completions(self, prefix, locations):
        """Sublime Text query completions event handler.

        Create a list with completions for all known settings or values.

        Arguments:
            prefix (string):
                the line content before cursor
            locations (list of int):
                the text positions of all characters in prefix

        Returns:
            tuple ([ [trigger, content], [trigger, content] ], flags):
                the tuple with content ST needs to display completions
        """
        if self.known_settings and len(locations) == 1:
            if self.view.match_selector(locations[0], VALUE_SCOPE):
                completions = self.known_settings.value_completions
            else:
                completions = self.known_settings.key_completions
            return completions(self.view, prefix, locations)

    def on_hover(self, point, hover_zone):
        """Sublime Text hover event handler to show tooltip if needed."""
        # not a settings file or not hovering text
        if not self.known_settings or hover_zone != sublime.HOVER_TEXT:
            return
        # settings key name under cursor
        key = key_name(self.view, point)
        if not key:
            return
        body = self.known_settings.tooltip(self.view, key)
        window_width = min(1000, int(self.view.viewport_extent()[0]) - 64)
        self.view.show_popup(
            content=POPUP_TEMPLATE.format(body), on_navigate=self.on_navigate,
            location=point, max_width=window_width,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY)

    def on_navigate(self, href):
        """Popup navigation event handler."""
        command, argument = href.split(':')
        if command == 'edit':
            view_id = self.view.settings().get('edit_settings_other_view_id')
            user_view = sublime.View(view_id)
            if not user_view.is_valid():
                return
            result = user_view.find(argument, 0)
            self.view.hide_popup()
            if self.view.window():
                self.view.window().focus_view(user_view)
            if result.a == -1:
                self.known_settings.insert_snippet(user_view, argument)
            else:
                user_view.sel().clear()
                user_view.show_at_center(result.end())
                user_view.sel().add(result.end() + 3)

    def do_linting(self):
        """Highlight all unknown settings keys."""
        unknown_regions = [
            region for region in self.view.find_by_selector(KEY_SCOPE)
            if self.view.substr(region).strip('"') not in self.known_settings
        ] if self.view.settings().get('settings_linting') else None
        if unknown_regions:
            self.view.add_regions(
                'unknown_settings_keys',
                unknown_regions,
                scope="markup.warning.unknown-key.sublime-settings",
                icon="dot",
                flags=sublime.DRAW_SOLID_UNDERLINE |
                sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE)
        else:
            self.view.erase_regions('unknown_settings_keys')


class KnownSettings(object):
    """A class which provides all known settings with comments/defaults.

    An object of this class initialized with a sublime-settings file loads all
    basefiles from all packages including comments and default values to
    provide all required information for tooltips and auto-completion.
    """

    def __init__(self, filename):
        """Initialize view event listener object."""
        basename = os.path.basename(filename)
        if not basename.lower().endswith(".sublime-settings"):
            raise ValueError('No Sublime Settings')
        # the associated settings file name all the settings belong to
        self.filename = basename
        # the dictionary with all comments of each setting
        self.comments = {}
        # the dictionary with all defaults of a setting
        self.defaults = {}
        self._load_settings()

    def __iter__(self):
        """Forward iteration to settings."""
        return self.defaults.__iter__()

    def __next__(self):
        """Forward iteration to settings."""
        return self.defaults.next()

    def _load_settings(self):
        """Load and merge settings and their comments from all base files.

        The idea is each package which wants to add a valid entry to the
        `Preferences.sublime-settings` file must provide such a file with all
        keys it wants to add. These keys and the associated comments above it
        are loaded into dictionaries and used to provide tooltips, completions
        and linting.
        """
        ignored_patterns = frozenset(('/User/', '/Preferences Editor/'))

        for resource in sublime.find_resources(self.filename):
            # skip ignored settings
            if any(ignored in resource for ignored in ignored_patterns):
                continue
            try:
                lines = sublime.load_resource(resource).splitlines()
                for key, value in self._parse_settings(lines).items():
                    # merge settings without overwriting existing ones
                    if key not in self.defaults:
                        self.defaults[key] = value
            except:
                pass

    def _parse_settings(self, lines):
        """Parse the setting file and capture comments."""
        content = []
        comment = []
        in_comment = False

        for line in lines:
            stripped = line.strip()
            # ignore empty lines
            if not stripped:
                continue

            if in_comment:
                if stripped.endswith("*/"):
                    in_comment = False
                    # remove all spaces and asterix
                    line = line.rstrip("*/ \t")
                    if line:
                        comment.append(line)
                elif stripped.startswith("* "):
                    comment.append(stripped[2:])
                else:
                    comment.append(line)
                continue

            if stripped.startswith("/*"):
                in_comment = True
                # remove all asterix
                stripped = stripped[2:].lstrip("*")
                if stripped:
                    comment.append(stripped)
                continue

            if stripped.startswith("//"):
                stripped = stripped[2:]
                if stripped:
                    comment.append(stripped)
                continue

            content.append(line)
            if comment:
                # the json key is used as key for the comments located above it
                key = stripped.split(':', 1)[0].strip(' \t"')
                if key not in self.comments:
                    self.comments[key] = textwrap.dedent('\n'.join(comment))
                comment.clear()
        # Return decoded json file from content with stripped comments
        return sublime.decode_value('\n'.join(content))

    def tooltip(self, view, key):
        """Return html encoded docstring for settings key.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            key (string):
                the key under the cursor
        """
        if key in self.defaults:
            # the comment for the setting
            comment = html_encode(self.comments.get(key) or 'No description.')
            # the default value from base file
            default = html_encode(
                sublime.encode_value(self.defaults.get(key), pretty=True))
            # prepare a link to add the settings to user file or jump to its
            # position for editing, if the item in side-by-side setting's
            # base view is hoverd
            if view.settings().get('edit_settings_view') == 'base':
                edit = '<a href="edit:{0}">✏</a>'.format(key)
            else:
                edit = ''
        else:
            comment, default, edit = 'No description.', 'unknown setting.', ''
        # format tooltip html content
        return (
            '<h1>{edit} {key}</h1>'
            '<h2>Default: {default}</h2>'
            '<p>{comment}</p>'
        ).format(**locals())

    def insert_snippet(self, view, key):
        """Insert a snippet for the settings key at the end of the view.

        Arguments:
            view (sublime.View):
                The view to add the snippet to. Doesn't need to be the view
                of this ViewEventHandler. It's more likely the view of the
                user settings which is to be passed here.
            key (string):
                The settings key to insert a snippet for.
        """
        # find last value in the view
        value_regions = view.find_by_selector(VALUE_SCOPE)
        if not value_regions:
            # no value found use end of global dict
            selector = 'meta.structure.dictionary'
            value_regions = view.find_by_selector(selector)
            if not value_regions:
                # no global dict found, insert one
                point = view.size()
                is_empty_line = not view.substr(view.line(point)).strip()
                bol = '{\n\t' if is_empty_line else '\n{\n\t'
                eol = '\n}\n'
            else:
                # insert first value to user file
                point = value_regions[-1].end() - 1
                bol, eol = '\t', '\n'
        else:
            point = value_regions[-1].end()
            if view.substr(point) == ',':
                # already have a comma after last entry
                eol, bol = '', '\n'
            else:
                # add a comma after last entry
                eol, bol = '', ',\n'
                point -= 1
        # format and insert the snippet
        snippet = self._key_snippet(key, self.defaults[key], bol, eol)
        view.sel().clear()
        view.sel().add(point)
        view.run_command('insert_snippet', {'contents': snippet})

    def key_completions(self, view, prefix, locations):
        """Create a list with completions for all known settings.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            prefix (string):
                the line content before cursor
            locations (list of int):
                the text positions of all characters in prefix

        Returns:
            tuple ([ [trigger, content], [trigger, content] ], flags):
                the tuple with content ST needs to display completions
        """
        if view.match_selector(locations[0] - 1, 'string'):
            # we are within quotations, return words only
            completions = [
                ['{0}  \tsetting'.format(key), '{0}'.format(key)]
                for key in self.defaults
            ]
        else:
            line = view.substr(view.line(locations[0])).strip()
            # don't add newline after snippet if user starts on empty line
            eol = ',' if len(line) == len(prefix) else ',\n'
            # no quotations -> return full snippet
            completions = [[
                '{0}  \tsetting'.format(key),
                self._key_snippet(key, value, eol=eol)
            ] for key, value in self.defaults.items()]
        return (completions, sublime.INHIBIT_WORD_COMPLETIONS)

    def _key_snippet(self, key, value, bol='', eol=',\n'):
        """Create snippet with default value depending on type.

        Arguments:
            key (string):
                the settings key name
            value (any):
                the default value of the setting read from base file
            bol (string):
                the prefix to add to the beginning of line
            eol (string):
                the suffix to add to the end of line

        Returns:
            string: the contents field to insert into completions entry
        """
        encoded = sublime.encode_value(value)
        if isinstance(value, str):
            # create he snippet for json strings and exclude quotation marks
            # from the input field {1:}
            #
            #   "key": "value"
            #
            fmt = '{bol}"{key}": "${{1:{encoded}}}"{eol}$0'
            encoded = encoded[1:-1]  # strip quotation
        elif isinstance(value, list):
            # create he snippet for json lists and exclude brackets
            # from the input field {1:}
            #
            #   "key":
            #   [
            #      value
            #   ]
            #
            fmt = '{bol}"{key}":\n[\n\t${{1:{encoded}}}\n]{eol}$0'
            encoded = encoded[1:-1]  # strip brackets
        elif isinstance(value, dict):
            # create he snippet for json dictionaries braces
            # from the input field {1:}
            #
            #   "key":
            #   {
            #      value
            #   }
            #
            fmt = '{bol}"{key}":\n{{\n\t${{1:{encoded}}}\n}}{eol}$0'
            encoded = encoded[1:-1]  # strip braces
        else:
            fmt = '{bol}"{key}": ${{1:{encoded}}}{eol}$0'
        return fmt.format(**locals())

    def value_completions(self, view, prefix, locations):
        """Create a list with completions for all known settings values.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            prefix (string):
                the line content before cursor.
            locations (list of int):
                the text positions of all characters in prefix

        Returns:
            tuple ([ [trigger, content], [trigger, content] ], flags):
                the tuple with content ST needs to display completions
        """
        point = locations[0]
        region = value_region(view, point)
        key = key_name(view, region.a - 2)
        default = self.defaults.get(key)
        # default value or list element is of type string
        is_str = (
            isinstance(default, str) or
            isinstance(default, list) and isinstance(default[0], str)
        )
        # cursor not yet within quotes, so need to add some by completions
        quote = is_str and not view.match_selector(point, 'string')

        if key == 'color_scheme':
            completions = self._colors_completions(view, quote)
        elif key == 'theme':
            completions = self._theme_completions(view, quote)
        else:
            # the value typed so far which may differ from prefix for floats
            typed = view.substr(sublime.Region(region.a + 1, point)).lstrip()
            # try to built the list of completions from setting's comment
            completions = list(self._comment_completions(
                view, key, default, typed, prefix, quote))
            if not completions:
                if isinstance(default, bool):
                    completions = [
                        ['true  \tboolean', 'true'],
                        ['false \tboolean', 'false']
                    ]
                elif default:
                    completions = [[
                        '{0}  \tdefault'.format(default),
                        '"{0}"'.format(default) if quote else str(default)
                    ]]
        # disable word completion to prevent stupid suggestions
        return (
            sorted(completions, key=lambda x: x[0].lower()),
            sublime.INHIBIT_WORD_COMPLETIONS)

    def _comment_completions(self, view, key, default, typed, prefix, quote):
        """Generator to parse settings comment and return all possible values.

        Many settings are commented with a list of quoted words representing
        the possible / allowed values. This method generates a list of these
        quoted words which are suggested in auto-completions.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            key (string):
                the settings key name to read comments from
            default (any):
                the default value of key
            typed (string):
                the value entered so far, which may differ from prefix if
                user entered floating point numbers
            prefix (string):
                the completion prefix provided by ST.
            quote (bool):
                True if completions need to be quoted.

        Yields:
            list: [trigger, contents]
                The list representing one auto-completion item.
        """
        is_float = isinstance(default, float)
        if is_float:
            # strip already entered '1.' from completions as ST doesn't
            offset = len(typed) - len(prefix)
        for match in re.finditer('"([\.\w]+)"', self.comments.get(key, '')):
            word, = match.groups()
            if is_float:
                # provide completions for numbers which match the already
                # entered value
                if word.startswith(typed):
                    yield ['{0}  \tnumber'.format(word), word[offset:]]
            else:
                yield [
                    '{0}  \tstring'.format(word),
                    '"{0}"'.format(word) if quote else word
                ]

    def _colors_completions(self, view, quote):
        """Create completions of all visible color schemes.

        The list will not include color schemes matching at least one entry of
        `"hidden_color_scheme_pattern": []` view setting.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            quote (bool):
                True if completions need to be quoted.

        Returns:
            list: [[trigger, contents], ...]
                The list of all completions.
                - trigger (string): base file name of the color scheme
                - contents (string): the path to commit to the settings
        """
        hidden = view.settings().get('hidden_color_scheme_pattern') or []
        completions = []
        for colors in sublime.find_resources('*.tmTheme'):
            if any(hide in colors for hide in hidden):
                continue
            item = [
                '{0}  \tcolors'.format(os.path.basename(colors)),
                '"{0}"'.format(colors) if quote else colors
            ]
            if item not in completions:
                completions.append(item)
        return completions

    def _theme_completions(self, view, quote):
        """Create completions of all visible themes.

        The list will not include color schemes matching at least one entry of
        `"hidden_theme_pattern": []` view setting.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            quote (bool):
                True if completions need to be quoted.

        Returns:
            list: [[trigger, contents], ...]
                The list of all completions.
                - trigger (string): base file name of the color scheme
                - contents (string): the file name to commit to the settings
        """
        hidden = view.settings().get('hidden_theme_pattern') or []
        completions = []
        for theme in sublime.find_resources('*.sublime-theme'):
            theme = os.path.basename(theme)
            if any(hide in theme for hide in hidden):
                continue
            item = [
                '{0}  \tthemes'.format(theme),
                '"{0}"'.format(theme) if quote else theme
            ]
            if item not in completions:
                completions.append(item)
        return completions
