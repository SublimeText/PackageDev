# -*- encoding: utf-8 -*-
import logging
import os
import re
import textwrap
import time

import sublime
import sublime_plugin

from .sublime_lib.constants import style_flags_from_list


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
        padding: 0.5rem 0.6rem;
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
KEY_SCOPE = "entity.name.other.key.sublime-settings"
VALUE_SCOPE = (
    "meta.expect-value | meta.mapping.value | "
    "punctuation.separator.mapping.pair.json"
)
# user package pattern
USER_PATH = "{0}Packages{0}User{0}".format(os.sep)

# logging
l = logging.getLogger(__name__)


def html_encode(string):
    """Encode some critical characters to html entities."""
    return string.replace("&", "&amp;")           \
                 .replace("<", "&lt;")            \
                 .replace(">", "&gt;")            \
                 .replace("\t", "&nbsp;&nbsp;")   \
                 .replace("    ", "&nbsp;&nbsp;") \
                 .replace("\n", "<br>") if string else ""


def get_key_region_at(view, point):
    """Return the key region if point is on a settings key or None."""
    if view.match_selector(point, KEY_SCOPE):
        for region in view.find_by_selector(KEY_SCOPE):
            if region.contains(point):
                return region
    return None


def get_key_name(view, point):
    """Return the key name if point is on a settings key or None."""
    region = get_key_region_at(view, point)
    return view.substr(region) if region else None


def get_last_key_name_from(view, point):
    """Return the last key name preceding the specified point or None."""
    last_region = None
    regions = view.find_by_selector(KEY_SCOPE)
    if not regions:
        return None
    for region in regions:
        # l.debug("comparing region %s to %d (contents: %r)", region,)
        if region.begin() > point:
            break
        last_region = region
    return view.substr(last_region)


def get_value_region_at(view, point):
    """Return the value region if point is on a settings value or None."""
    if view.match_selector(point, VALUE_SCOPE):
        for region in view.find_by_selector(VALUE_SCOPE):
            if region.contains(point):
                return region
    return None


def sorted_completions(completions):
    return list(sorted(completions, key=lambda x: x[0].lower()))


def int_or_float(string):
    try:
        return int(string)
    except ValueError:
        return float(string)


def _settings():
    """Return global package settings object or load it first if required."""
    try:
        return _settings.settings
    except AttributeError:
        l.debug("Loading PackageDev.sublime-settings")
        _settings.settings = sublime.load_settings("PackageDev.sublime-settings")
        return _settings.settings


class SettingsListener(sublime_plugin.ViewEventListener):

    @classmethod
    def is_applicable(cls, settings):
        """Enable the listener for Sublime Settings syntax only."""
        # view is member of side-by-side settings
        if settings.get('edit_settings_view') in ('base', 'user'):
            # l.debug("view is member of side-by-side settings")  # too spammy
            return True
        else:
            syntax = settings.get('syntax', "")
            return syntax.endswith("/Sublime Text Settings.sublime-syntax")

    def __init__(self, view):
        """Initialize view event listener object."""
        super(SettingsListener, self).__init__(view)
        self.known_settings = None

        filepath = view.file_name()
        l.debug("initializing SettingsListener for %r", view.file_name())
        if not filepath.endswith(".sublime-settings"):
            l.error("Not a Sublime Text Settings file: %r", filepath)
        else:
            filename = os.path.basename(filepath)
            self.known_settings = KnownSettings(filename, on_loaded=self.do_linting)

    def __del__(self):
        l.debug("deleting SettingsListener instance for %r", self.view.file_name())
        self.view.erase_regions('unknown_settings_keys')

    def on_modified_async(self):
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
                completions_aggregator = self.known_settings.value_completions
            else:
                completions_aggregator = self.known_settings.key_completions
            return completions_aggregator(self.view, prefix, locations)

    def on_hover(self, point, hover_zone):
        """Sublime Text hover event handler to show tooltip if needed."""
        # not a settings file or not hovering text
        if not self.known_settings or hover_zone != sublime.HOVER_TEXT:
            return
        # settings key name under cursor
        key_region = get_key_region_at(self.view, point)
        if not key_region:
            return
        key = self.view.substr(key_region)

        body = self.known_settings.build_tooltip(self.view, key)
        window_width = min(1000, int(self.view.viewport_extent()[0]) - 64)
        # offset <h1> padding, if possible
        key_start = key_region.begin()
        location = max(key_start - 1, self.view.line(key_start).begin())

        self.view.show_popup(
            content=POPUP_TEMPLATE.format(body),
            on_navigate=self.on_navigate,
            location=location,
            max_width=window_width,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY
        )

    def on_navigate(self, href):
        """Popup navigation event handler."""
        command, argument = href.split(":")
        if command == 'edit':
            view_id = self.view.settings().get('edit_settings_other_view_id')
            user_view = sublime.View(view_id)
            if not user_view.is_valid():
                return
            result = user_view.find('"{}"'.format(argument), 0)
            self.view.hide_popup()
            if self.view.window():
                self.view.window().focus_view(user_view)
            if result.a == -1:
                self.known_settings.insert_snippet(user_view, argument)
            else:
                user_view.sel().clear()
                user_view.show_at_center(result.end())
                user_view.sel().add(result.end() + 2)

    def do_linting(self):
        """Highlight all unknown settings keys."""
        unknown_regions = None
        if (
            USER_PATH in self.view.file_name()
            and _settings().get('settings.linting')
            and self.known_settings
        ):
            unknown_regions = [
                region for region in self.view.find_by_selector(KEY_SCOPE)
                if self.view.substr(region) not in self.known_settings
            ]

        if unknown_regions:
            styles = _settings().get('settings.highlight_styles',
                                     ['DRAW_SOLID_UNDERLINE', 'DRAW_NO_FILL', 'DRAW_NO_OUTLINE'])
            self.view.add_regions(
                'unknown_settings_keys',
                unknown_regions,
                scope=_settings().get('settings.highlight_scope', "text"),
                icon='dot',
                flags=style_flags_from_list(styles)
            )
        else:
            self.view.erase_regions('unknown_settings_keys')


# TODO cache these (by filename) to reduce load
class KnownSettings(object):
    """A class which provides all known settings with comments/defaults.

    An object of this class initialized with a sublime-settings file loads all
    basefiles from all packages including comments and default values to
    provide all required information for tooltips and auto-completion.
    """

    def __init__(self, filename, on_loaded=None):
        """Initialize view event listener object.

        Arguments:
            filename (str):
                Settings file name to index.
            on_loaded (callable):
                Function to call once settings have been indexed.
        """
        # the associated settings file name all the settings belong to
        self.filename = filename
        self.on_loaded = on_loaded

        self.trigger_settings_reload()

    def __iter__(self):
        """Forward iteration to settings."""
        return self.defaults.__iter__()

    def __next__(self):
        """Forward iteration to settings."""
        return self.defaults.next()

    def trigger_settings_reload(self):
        # the dictionary with all defaults of a setting
        self.defaults = {}
        # the dictionary with all comments of each setting
        self.comments = {}
        # look for settings files asynchronously
        sublime.set_timeout_async(self._load_settings, 0)

    def _load_settings(self):
        """Load and merge settings and their comments from all base files.

        The idea is each package which wants to add a valid entry to the
        `Preferences.sublime-settings` file must provide such a file with all
        keys it wants to add. These keys and the associated comments above it
        are loaded into dictionaries and used to provide tooltips, completions
        and linting.
        """
        ignored_patterns = frozenset(("/User/", "/Preferences Editor/"))

        # TODO project settings include "Preferences",
        # but we don't have a syntax def for those yet
        l.debug("loading defaults and comments for %r", self.filename)
        start_time = time.time()
        resources = sublime.find_resources(self.filename)
        resources += sublime.find_resources(self.filename + "-hints")
        l.debug("found %d %r files", len(resources), self.filename)

        # include general settings if we're in a syntax-specific file
        if self._is_syntax_specific():
            # TODO fetch these from cache, once we have one
            pref_resources = sublime.find_resources("Preferences.sublime-settings")
            pref_resources += sublime.find_resources("Preferences.sublime-settings-hints")
            l.debug("found %d 'Preferences.sublime-settings' files", len(pref_resources))
            resources += pref_resources

        for resource in resources:
            # skip ignored settings
            if any(ignored in resource for ignored in ignored_patterns):
                continue
            try:
                l.debug("parsing %r", resource)
                lines = sublime.load_resource(resource).splitlines()
                for key, value in self._parse_settings(lines).items():
                    # merge settings without overwriting existing ones
                    self.defaults.setdefault(key, value)
            except Exception as e:
                l.error("error parsing %r - %s%s", resource, e.__class__.__name__, e.args)

        duration = time.time() - start_time
        l.debug("loading took %.3fs", duration)

        if self.on_loaded:
            self.on_loaded()

    def _is_syntax_specific(self):
        """Check whether a syntax def with the same base file name exists.

        Returns:
            bool
        """
        syntax_file_exts = (".sublime-syntax", ".tmLanguage")
        name_no_ext = os.path.splitext(self.filename)[0]
        for ext in syntax_file_exts:
            syntax_file_name = name_no_ext + ext
            resources = sublime.find_resources(syntax_file_name)
            if resources:
                l.debug("syntax-specific settings file for %r", resources[0])
                return True
        else:
            return False

    def _parse_settings(self, lines):
        """Parse the setting file and capture comments.

        This is naive but gets the job done most of the time.
        """
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
                if stripped.endswith("//"):
                    # skip comment lines ending with `//` (likely used as separators)
                    continue
                stripped = stripped[2:]
                if stripped:
                    comment.append(stripped)
                continue

            content.append(line)
            if comment:
                # the json key is used as key for the comments located above it
                match = re.match(r'"((?:[^"]|\\.)*)":', stripped)
                if not match:
                    continue
                key = match.group(1)

                if key not in self.comments:
                    self.comments[key] = textwrap.dedent('\n'.join(comment))
                comment.clear()

        # Return decoded json file from content with stripped comments
        return sublime.decode_value('\n'.join(content))

    def build_tooltip(self, view, key):
        """Return html encoded docstring for settings key.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            key (string):
                the key under the cursor
        """
        if key in self.defaults:
            # the comment for the setting
            comment = html_encode(self.comments.get(key) or "No description.")
            # the default value from base file
            default = html_encode(
                sublime.encode_value(self.defaults.get(key), pretty=True))
            # prepare a link to add the settings to user file or jump to its
            # position for editing, if the item in side-by-side setting's
            # base view is hoverd
            if view.settings().get('edit_settings_view') == 'base':
                edit = "<a href=\"edit:{0}\">✏</a>".format(key)
            else:
                edit = ""
        else:
            comment, default, edit = "No description.", "unknown setting", ""
        # format tooltip html content
        return (
            "<h1>{key} {edit}</h1>"
            "<h2>Default: {default}</h2>"
            "<p>{comment}</p>"
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
            selector = "meta.mapping"
            value_regions = view.find_by_selector(selector)
            if not value_regions:
                # no global dict found, insert one
                point = view.size()
                is_empty_line = not view.substr(view.line(point)).strip()
                bol = "{\n\t" if is_empty_line else "\n{\n\t"
                eol = "\n}\n"
            else:
                # insert first value to user file
                point = value_regions[-1].end() - 1
                bol, eol = "\t", "\n"
        else:
            point = value_regions[-1].end()
            if view.substr(point) == ",":
                # already have a comma after last entry
                eol, bol = "", "\n"
                point += 1
            else:
                # add a comma after last entry
                eol, bol = "", ",\n"
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
        if view.match_selector(locations[0] - 1, "string"):
            # we are within quotations, return words only
            completions = [
                ["{0}  \tsetting".format(key), '{0}'.format(key)]
                for key in self.defaults
            ]
        else:
            line = view.substr(view.line(locations[0])).strip()
            # don't add newline after snippet if user starts on empty line
            eol = "," if len(line) == len(prefix) else ',\n'
            # no quotations -> return full snippet
            completions = [[
                "{0}  \tsetting".format(key),
                self._key_snippet(key, value, eol=eol)
            ] for key, value in self.defaults.items()]
        return (completions, sublime.INHIBIT_WORD_COMPLETIONS)

    @staticmethod
    def _key_snippet(key, value, bol="", eol=",\n"):
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
            # create the snippet for json strings and exclude quotation marks
            # from the input field {1:}
            #
            #   "key": "value"
            #
            fmt = '{bol}"{key}": "${{1:{encoded}}}"{eol}$0'
            encoded = encoded[1:-1]  # strip quotation
        elif isinstance(value, list):
            # create the snippet for json lists and exclude brackets
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
            # create the snippet for json dictionaries braces
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
        value_region = get_value_region_at(view, point)
        key = get_last_key_name_from(view, value_region.begin())
        if not key:
            l.debug("unable to find current key")
            return None
        l.debug("building completions for key %r", key)
        default = self.defaults.get(key)

        if key == 'color_scheme':
            completions = self._color_scheme_completions(view)
        elif key == 'theme':
            completions = self._theme_completions(view)
        else:
            # the value typed so far which may differ from prefix for floats
            typed_region = sublime.Region(value_region.begin(), point)
            typed = view.substr(typed_region).lstrip()
            # try to built the list of completions from setting's comment
            completions = self._completions_from_comment(view, key)

            if not completions:
                if isinstance(default, bool):
                    completions = [
                        ["false \tboolean", False],
                        ["true  \tboolean", True],
                    ]
                    completions[default][0] += " (default)"  # booleans are integers

                elif default:
                    completions = [(
                        "{}  \t{} (default)".format(default, type(default).__name__),
                        default
                    )]

                else:
                    # nothing to offer
                    return None

        is_str = bool(
            # default value is of type string
            isinstance(default, str)
            # the list elements of default are of type string
            or isinstance(default, list) and default and isinstance(default[0], str)
            # the offered completions are of type string
            or completions and isinstance(completions[0][1], str)
        )
        # cursor already within quotes
        in_str = view.match_selector(point, "string")
        l.debug("completing a string (%s) within a string (%s)", is_str, in_str)

        if not in_str or not is_str:
            # jsonify completion values
            completions_tmp = []
            for trigger, value in completions:
                if isinstance(value, float):
                    # strip already typed text from float completions
                    # because ST cannot complete past word boundaries
                    # (e.g. strip `1.` of `1.234`)
                    value_str = str(value)
                    if value_str.startswith(typed):
                        offset = len(typed) - len(prefix)
                        completions.append((
                            "{0}\tfloat".format(value),
                            value_str[offset:]
                        ))
                else:
                    completions_tmp.append((trigger, sublime.encode_value(value)))
            completions = completions_tmp
        elif is_str and in_str:
            # Strip completions of non-strings. Don't need quotation marks.
            completions = [(trigger, value)
                           for trigger, value in completions
                           if isinstance(value, str)]
        else:
            # We're within a string but don't have a string value to complete.
            # Complain about this in the status bar, I guess.
            msg = "Cannot complete value set within a string"
            view.window().status_message(msg)
            l.warning(msg)
            return None

        # disable word completion to prevent stupid suggestions
        return sorted_completions(completions), sublime.INHIBIT_WORD_COMPLETIONS

    def _completions_from_comment(self, view, key):
        """Parse settings comments and return all possible values.

        Many settings are commented with a list of quoted words representing
        the possible / allowed values. This method generates a list of these
        quoted words which are suggested in auto-completions.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            key (string):
                the settings key name to read comments from

        Yields:
            list: [trigger, contents]
                The list representing one auto-completion item.
        """
        comment = self.comments.get(key, '')
        if not comment:
            return

        # must use list because "lists" as values are not hashable
        values = []
        for match in re.finditer(r"`([^`\n]+)`", comment):
            # backticks should wrap the value in JSON representation,
            # so we try to decode it
            value_str, = match.groups()
            try:
                value = sublime.decode_value(value_str)
            except:
                value = value_str
            values.append(value)

        for match in re.finditer(r'"([\.\w]+)"', comment):
            # quotation marks either wrap a string, a numeric or a boolean
            # fall back to a str
            value, = match.groups()
            if value == "true":
                value = True
            elif value == "false":
                value = False
            else:
                try:
                    value = int_or_float(value)
                except ValueError:
                    pass  # just use the string
            values.append(value)

        completions = [("{}  \t{}".format(value, type(value).__name__), value)
                       for value in values]
        return sorted_completions(completions)

    @staticmethod
    def _color_scheme_completions(view):
        """Create completions of all visible color schemes.

        The list will not include color schemes matching at least one entry of
        `"hidden_color_scheme_pattern": []` view setting.

        Arguments:
            view (sublime.View):
                the view to provide completions for

        Returns:
            list: [[trigger, contents], ...]
                The list of all completions.
                - trigger (string): base file name of the color scheme
                - contents (string): the path to commit to the settings
        """
        hidden = _settings().get('settings.exclude_color_scheme_patterns') or []
        completions = []
        for scheme_path in sublime.find_resources("*.tmTheme"):
            if any(hide in scheme_path for hide in hidden):
                continue
            _, package, *_, file_name = scheme_path.split("/")
            completions.append((
                "{}: {}  \tcolors".format(package, file_name), scheme_path))
        return completions

    @staticmethod
    def _theme_completions(view):
        """Create completions of all visible themes.

        The list will not include color schemes matching at least one entry of
        `"hidden_theme_pattern": []` view setting.

        Arguments:
            view (sublime.View):
                the view to provide completions for

        Returns:
            list: [[trigger, contents], ...]
                The list of all completions.
                - trigger (string): base file name of the color scheme
                - contents (string): the file name to commit to the settings
        """
        hidden = _settings().get('settings.exclude_theme_patterns') or []
        completions = []
        for theme in sublime.find_resources("*.sublime-theme"):
            theme = os.path.basename(theme)
            if any(hide in theme for hide in hidden):
                continue
            completions.append(("{}  \ttheme".format(theme), theme))
        return sorted_completions(completions)
