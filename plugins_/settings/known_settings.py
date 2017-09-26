import collections
import logging
import os
import re
import textwrap
import time
import weakref

import sublime

from ..lib.weakmethod import WeakMethodProxy
from ..lib import get_setting, sorted_completions
from .region_math import VALUE_SCOPE, get_value_region_at, get_last_key_name_from

l = logging.getLogger(__name__)

PREF_FILE = "Preferences.sublime-settings"


def html_encode(string):
    """Encode some critical characters to html entities."""
    return string.replace("&", "&amp;")           \
                 .replace("<", "&lt;")            \
                 .replace(">", "&gt;")            \
                 .replace("\t", "&nbsp;&nbsp;")   \
                 .replace("    ", "&nbsp;&nbsp;") \
                 .replace("\n", "<br>") if string else ""


def format_completion_item(value, default=False):
    """Create a completion item with its type as description."""
    if isinstance(value, dict):
        raise ValueError("Cannot format dictionary value", value)
    default_str = "(default) " if default else ""
    return ("{0}  \t{2}{1}".format(sublime.encode_value(value).strip('"'),
                                   type(value).__name__,
                                   default_str),
            value)


def decode_value(string):
    """Decode string to python object with unrestrictive booleans."""
    if string.lower() == "true":
        return True
    if string.lower() == "false":
        return False
    try:
        return int(string)
    except ValueError:
        return float(string)


class KnownSettings(object):
    """A class which provides all known settings with comments/defaults.

    An object of this class initialized with a sublime-settings file loads all
    basefiles from all packages including comments and default values to
    provide all required information for tooltips and auto-completion.
    """

    # cache for instances, keyed by the basename
    # and using weakrefs for easy garbage collection
    cache = weakref.WeakValueDictionary()

    _is_initialized = False
    _is_loaded = False
    filename = None
    on_loaded_callbacks = None
    on_loaded_once_callbacks = None
    defaults = None
    comments = None
    fallback_settings = None

    def __new__(cls, filename, on_loaded=None, **kwargs):
        # __init__ will be called on the return value
        obj = cls.cache.get(filename)
        if obj:
            l.debug("cache hit %r", filename)
            return cls.cache[filename]
        else:
            obj = super().__new__(cls, **kwargs)
            cls.cache[filename] = obj
            return obj

    def __init__(self, filename):
        """Initialize view event listener object.

        Arguments:
            filename (str):
                Settings file name to index.
        """
        # Because __init__ may be called multiple times
        # and we only want to trigger a reload once,
        # we need special handling here.
        if not self._is_initialized:
            # the associated settings file name all the settings belong to
            self.filename = filename
            # callback lists
            self.on_loaded_callbacks = []
            self.on_loaded_once_callbacks = []
            self._is_initialized = True
            # the dictionary with all defaults of a setting
            self.defaults = collections.ChainMap()
            # the dictionary with all comments of each setting
            self.comments = collections.ChainMap()

            self.trigger_settings_reload()

    def add_on_loaded(self, on_loaded, once=False):
        """Add a callback to call once settings have been indexed (asynchronously).

        Bound methods are stored as weak references.

        Arguments:
            on_loaded (callable):
                The callback.
            once (bool):
                Whether the callback should be called only once.
        """
        # Due to us archiving the callback, we use a weakref
        # to avoid a circular reference to all SettingListeners affected,
        # ensuring our __del__ is properly called when all relevant views are closed.
        if self._is_loaded:
            # Invoke callback 'immediately' since we're already loaded.
            # Note that this is currently not thread-safe.
            sublime.set_timeout_async(on_loaded, 0)

        if not once:
            self.on_loaded_callbacks.append(WeakMethodProxy(on_loaded))
        elif not self._is_loaded:
            self.on_loaded_once_callbacks.append(WeakMethodProxy(on_loaded))

    def __del__(self):
        l.debug("deleting KnownSettings instance for %r", self.filename)

    def __iter__(self):
        """Iterate over default keys."""
        return iter(self.defaults)

    def trigger_settings_reload(self):
        # look for settings files asynchronously
        sublime.set_timeout_async(self._load_settings, 0)

    def _load_settings(self, on_loaded_once=None):
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

        for resource in resources:
            if any(ignored in resource for ignored in ignored_patterns):
                l.debug("ignoring %r", resource)
                continue

            try:
                l.debug("parsing %r", resource)
                lines = sublime.load_resource(resource).splitlines()
                for key, value in self._parse_settings(lines).items():
                    # merge settings without overwriting existing ones
                    self.defaults.setdefault(key, value)
            except Exception as e:
                l.error("error parsing %r - %s%s",
                        resource, e.__class__.__name__, e.args)

        duration = time.time() - start_time
        l.debug("loading took %.3fs", duration)

        # include general settings if we're in a syntax-specific file
        is_syntax_specific = self._is_syntax_specific()
        if is_syntax_specific and not self.fallback_settings:
            self.fallback_settings = KnownSettings(PREF_FILE)
            # add fallbacks to the ChainMaps
            self.defaults.maps.append(self.fallback_settings.defaults)
            self.comments.maps.append(self.fallback_settings.comments)
            # these may be loaded later, so delay calling our own callbacks
            self.fallback_settings.add_on_loaded(self._has_loaded, once=True)
        else:
            if self.fallback_settings and not is_syntax_specific:
                # file was renamed, probably
                self.fallback_settings = None
                self.defaults.maps.pop()
                self.comments.maps.pop()
            self._has_loaded()

    def _has_loaded(self):
        self._is_loaded = True

        for callback in self.on_loaded_once_callbacks:
            try:
                callback()
            except ReferenceError:
                pass
        self.on_loaded_once_callbacks.clear()

        # copy callback list so we can clean up expired references
        for callback in tuple(self.on_loaded_callbacks):
            try:
                callback()
            except ReferenceError:
                l.debug("removing gone-away weak on_loaded_callback reference")
                self.on_loaded_callbacks.remove(callback)

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
            # ignore empty lines if not in a comment
            # empty line in comment may be used as visual separator
            elif not stripped:
                continue

            if stripped.startswith("/*"):
                in_comment = True
                # remove all asterix
                stripped = stripped[2:].lstrip("*")
                if stripped:
                    comment.append(stripped)
                continue

            if stripped.startswith("//"):
                # skip comment lines ending with `//` (likely used as separators)
                # a standalone `//` adds an empty line as visual separator
                stripped = stripped[2:]
                if not stripped or not stripped.endswith("//"):
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
        else:
            comment, default = "No description.", "unknown setting"
        # format tooltip html content
        return (
            "<h1>{key}</h1>"
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
                eol = ",$0\n}\n"
            else:
                # insert first value to user file
                point = value_regions[-1].end() - 1
                bol, eol = "\t", "\n"
        else:
            point = value_regions[-1].end()
            # Due to the scope selector,
            # the comma will always be the last character of the last region found,
            # if it exists.
            if view.substr(point - 1) == ",":
                # already have a comma after last entry
                bol, eol = "\n", ","
            else:
                # add a comma after last entry
                bol, eol = ",\n", ""
        # format and insert the snippet
        snippet = self._key_snippet(key, self.defaults[key], bol, eol)
        view.sel().clear()
        view.sel().add(point)
        view.run_command('insert_snippet', {'contents': snippet})

    def key_completions(self, view, prefix, point):
        """Create a list with completions for all known settings.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            prefix (string):
                the line content before cursor
            point (int):
                the text positions of all characters in prefix

        Returns:
            tuple ([ (trigger, content), (trigger, content) ], flags):
                the tuple with content ST needs to display completions
        """
        if view.match_selector(point - 1, "string"):
            # we are within quotations, return words only
            completions = [
                ["{0}  \tsetting".format(key), '{0}'.format(key)]
                for key in self.defaults
            ]
        else:
            line = view.substr(view.line(point)).strip()
            # don't add newline after snippet if user starts on empty line
            eol = "," if len(line) == len(prefix) else ',\n'
            # no quotations -> return full snippet
            completions = sorted_completions((
                "{0}  \tsetting".format(key),
                self._key_snippet(key, value, eol=eol)
            ) for key, value in self.defaults.items())

        return completions, sublime.INHIBIT_WORD_COMPLETIONS

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
        encoded = encoded.replace("\\", "\\\\")  # escape snippet markers
        encoded = encoded.replace("$", "\\$")
        encoded = encoded.replace("}", "\\}")

        if isinstance(value, str):
            # create the snippet for json strings and exclude quotation marks
            # from the input field {1:}
            #
            #   "key": "value"
            #
            fmt = '{bol}"{key}": "${{1:{encoded}}}"{eol}'
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
            fmt = '{bol}"{key}":\n[\n\t${{1:{encoded}}}\n]{eol}'
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
            fmt = '{bol}"{key}":\n{{\n\t${{1:{encoded}}}\n}}{eol}'
            encoded = encoded[1:-1]  # strip braces
        else:
            fmt = '{bol}"{key}": ${{1:{encoded}}}{eol}'
        return fmt.format(**locals())

    def value_completions(self, view, prefix, point):
        """Create a list with completions for all known settings values.

        Arguments:
            view (sublime.View):
                the view to provide completions for
            prefix (string):
                the line content before cursor.
            point (int):
                the text positions of all characters in prefix

        Returns:
            tuple ([ (trigger, content), (trigger, content) ], flags):
                the tuple with content ST needs to display completions
        """
        value_region = get_value_region_at(view, point)
        if not value_region:
            l.debug("unable to find current key region")
            return None

        key = get_last_key_name_from(view, value_region.begin())
        if not key:
            l.debug("unable to find current key")
            return None

        completions = self._value_completions_for(key)
        if not completions:
            l.debug("no completions to offer")
            return None

        is_str = any(bool(
            isinstance(value, str)
            or isinstance(value, list) and value and isinstance(value[0], str)
        ) for _, value in completions)
        # cursor already within quotes
        in_str = view.match_selector(point, "string")
        l.debug("completing a string (%s) within a string (%s)", is_str, in_str)
        # 'meta.structure.array' is used in the default JSON syntax
        # (PR pending: https://github.com/sublimehq/Packages/pull/862)
        is_list = isinstance(self.defaults.get(key), list)
        in_list = view.match_selector(point, "meta.sequence | meta.structure.array")
        l.debug("completing a list item (%s) within a list (%s)", is_list, in_list)

        if in_str and not is_str:
            # We're within a string but don't have a string value to complete.
            # Complain about this in the status bar, I guess.
            msg = "Cannot complete value set within a string"
            view.window().status_message(msg)
            l.warning(msg)
            return None

        if in_str and is_str:
            # Strip completions of non-strings. Don't need quotation marks.
            results = {
                (trigger, value) for trigger, value in completions
                if isinstance(value, str)
            }
        else:
            # JSON-ify completion values with special handling for floats.
            #
            # the value typed so far, which may differ from prefix for floats
            typed_region = sublime.Region(value_region.begin(), point)
            typed = view.substr(typed_region).lstrip()
            results = set()
            for trigger, value in completions:
                # unroll dicts
                if isinstance(value, frozenset):
                    value = dict(value)

                if isinstance(value, float):
                    # strip already typed text from float completions
                    # because ST cannot complete past word boundaries
                    # (e.g. strip `1.` of `1.234`)
                    value_str = str(value)
                    if value_str.startswith(typed):
                        offset = len(typed) - len(prefix)
                        value_str = value_str[offset:]
                    elif typed:
                        # don't offer as completion if 'typed' didn't match
                        continue
                else:
                    value_str = sublime.encode_value(value)

                if is_list and not in_list:
                    # wrap each item in a brackets to insert a 'list'
                    value_str = "[{}]".format(value_str)

                # escape snippet markers
                value_str = value_str.replace("$", "\\$")

                results.add((trigger, value_str))

        # disable word completion to prevent stupid suggestions
        return sorted_completions(results), sublime.INHIBIT_WORD_COMPLETIONS

    def _value_completions_for(self, key):
        """Collect and return value completions from matching source.

        Arguments:
            key (string):
                the settings key name to read comments from

        Returns:
            {(trigger, contents), ...}
                A set of all completions.
        """
        if key == 'color_scheme':
            completions = self._color_scheme_completions()
        elif key == 'theme':
            completions = self._theme_completions()
        else:
            l.debug("building completions for key %r", key)
            default = self.defaults.get(key)
            l.debug("default value: %r", default)
            completions = self._completions_from_comment(key)
            completions |= self._completions_from_default(key, default)
            completions = self._marked_default_completions(completions, default)
        return completions

    def _marked_default_completions(self, completions, default):
        """Mark completion items as default.

        For a list as default value, mark all of its values as default.

        Arguments:
            completions (set):
                The set with the completion items.

            default (Any):
                The default value (can also be a list).

        Returns:
            {(trigger, contents), ...}
                A set of all completions with defaults marked.
        """
        default_completions = set()
        is_list = isinstance(default, list)
        for item in completions:
            value = item[1]
            if is_list and value in default or value == default:
                item = format_completion_item(value, default=True)
            default_completions.add(item)
        return default_completions

    def _completions_from_comment(self, key):
        """Parse settings comments and return all possible values.

        Many settings are commented with a list of quoted words representing
        the possible / allowed values. This method generates a list of these
        quoted words which are suggested in auto-completions.

        Arguments:
            key (string):
                the settings key name to read comments from

        Returns:
            {(trigger, contents), ...}
                A set of all completions.
        """
        completions = set()
        comment = self.comments.get(key)
        if not comment:
            return completions

        for match in re.finditer(r"`([^`\n]+)`", comment):
            # backticks should wrap the value in JSON representation,
            # so we try to decode it
            value, = match.groups()
            try:
                value = sublime.decode_value(value)
            except ValueError:
                pass
            if isinstance(value, list):
                # Suggest list items as completions instead of a string
                # representation of the list.
                # Unless it's a dict.
                completions.update(format_completion_item(v) for v in value
                                   if not isinstance(v, dict))
            elif isinstance(value, dict):
                # TODO what should we do with dicts?
                pass
            else:
                completions.add(format_completion_item(value))

        for match in re.finditer(r'"([\.\w]+)"', comment):
            # quotation marks either wrap a string, a numeric or a boolean
            # fall back to a str
            value, = match.groups()
            try:
                value = decode_value(value)
            except ValueError:
                pass
            completions.add(format_completion_item(value))

        return completions

    def _completions_from_default(self, key, default):
        """Built completions from default value.

        Arguments:
            key (string):
                the settings key name to read comments from

        Returns:
            {(trigger, contents), ...}
                A set of all completions.
        """
        if default is None or default is "":
            return set()
        elif isinstance(default, bool):
            return {format_completion_item(True), format_completion_item(False)}
        elif isinstance(default, list):
            return {format_completion_item(value) for value in default}
        elif isinstance(default, dict):
            return set()  # TODO can't complete these yet
        else:
            return {format_completion_item(default)}

    @staticmethod
    def _color_scheme_completions():
        """Create completions of all visible color schemes.

        The set will not include color schemes matching at least one entry of
        `"settings.exclude_color_scheme_patterns": []`.

        Returns:
            {(trigger, contents], ...}
                A set of all completions.
                - trigger (string): base file name of the color scheme
                - contents (string): the path to commit to the settings
        """
        hidden = get_setting('settings.exclude_color_scheme_patterns') or []
        completions = set()
        for scheme_path in sublime.find_resources("*.tmTheme"):
            if not any(hide in scheme_path for hide in hidden):
                _, package, *_, file_name = scheme_path.split("/")
                completions.add((
                    "{0}  \t{1}".format(file_name, package), scheme_path))
        return completions

    @staticmethod
    def _theme_completions():
        """Create completions of all visible themes.

        The set will not include color schemes matching at least one entry of
        `"settings.exclude_theme_patterns": []` setting.

        Returns:
            {(trigger, contents), ...}
                A set of all completions.
                - trigger (string): base file name of the theme
                - contents (string): the file name to commit to the settings
        """
        hidden = get_setting('settings.exclude_theme_patterns') or []
        completions = set()
        for theme in sublime.find_resources("*.sublime-theme"):
            theme = os.path.basename(theme)
            if not any(hide in theme for hide in hidden):
                completions.add(("{0}  \ttheme".format(theme), theme))
        return completions
