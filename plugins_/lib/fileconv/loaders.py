import re
import os

import json
import yaml
import plistlib

import sublime

from ..sublime_lib.view import OutputPanel, coorded_substr, base_scope, get_text
from ..sublime_lib.path import file_path_tuple


# xml.parsers.expat is not available on certain Linux dists, use plist_parser then.
# See https://github.com/SublimeText/AAAPackageDev/issues/19
try:
    from xml.parsers.expat import ExpatError, ErrorString
except ImportError:
    from . import plist_parser
    use_plistlib = False
    print("[PackageDev] 'xml.parsers.expat' module not available; "
          "Falling back to bundled 'plist_parser'...")
else:
    use_plistlib = True

###############################################################################

re_js_comments_str = r"""
    (                               # Capture code
        (?:
            "(?:\\.|[^"\\])*"           # String literal
            |
            '(?:\\.|[^'\\])*'           # String literal
            |
            (?:[^/\n"']|/[^/*\n"'])+    # Any code besides newlines or string literals
            |
            \n                          # Newline
        )+                          # Repeat
    )|
    (/\* (?:[^*]|\*[^/])* \*/)      # Multi-line comment
    |
    (?://(.*)$)                     # Comment
"""
re_js_comments = re.compile(re_js_comments_str, re.VERBOSE + re.MULTILINE)


def strip_js_comments(string):
    """Originally obtained from Stackoverflow this function strips JavaScript
    (and JSON) comments from a string while considering those encapsulated by strings.

    http://stackoverflow.com/questions/2136363/matching-one-line-javascript-comments-with-re
    """
    parts = re_js_comments.findall(string)
    # Stripping the whitespaces is, of course, optional, but the columns are fucked up anyway
    # with the comments being removed and it doesn't break things.
    return ''.join(x[0].strip(' ') for x in parts)

###############################################################################


# Define the prototype loader class and the loaders for the separate data types
class LoaderProto(object):
    """Prototype class for data loaders of different types.

        Classes derived from this class (and in this file) will be appended
        to the module's ``get`` variable (a dict) with ``self.ext`` as their key.

        Variables to define:

            name (str)
                The loaders name, e.g. "JSON" or "Property List".

            ext (str)
                The default file extension. Used to construct ``self.ext_regex``.

            comment (str; optional)
                The line comment string for the file type. Used to construct
                ``self.opt_regex``.

            scope (str; optional)
                If the view's base scope equals this the file will be considered
                "valid" and then parsed.

            file_regex (str; optional)
                Regex to be applied to your output string in ``parse()``.

                This is used to determine the problem's position in the file and
                lets the user browse the errors with F4 and Shift+F4.
                Define up to three groups:
                    1: file path
                    2: line number
                    3: column

                For reference, see the "result_file_regex" key in a view's
                settings() or compare to build systems.

            output_panel_name (str; optional)
                If this is specified it will be used as the output panel's
                reference name.

                Defaults to ``"package_dev"``.

            ext_regex (str; optional)
                This regex will be used by get_ext_appendix() to determine the
                extension's appendix. The appendix should be found in group 1.

                Defaults to ``r'(?i)\.%s(?:-([^\.]+))?$' % self.ext``.

            opt_regex (str; optional)
                A regex to search for an option dict in a line. Used by
                ``self.get_options()`` and ``cls.load_options(view)``.
                Content should be found in group 1.

                Defaults to ``r'^\s*%s\s+\[PackageDev\]\s+(.+)$' % cls.comment``.


        Methods to implement:

            parse(self, *args, **kwargs)
                This is called when the actual parsing should happen.

                The file to be read from is defined in ``self.file_path``.
                The parsed data should be returned.
                To output problems, use ``self.output.write_line(str)`` and use a
                string matched by ``self.file_regex`` if possible.

                *args, **kwargs parameters are passed from
                ``load(self, *args, **kwargs)``. If you want to specify any options
                or optional parsing, use these.

        Methods you can override/implement
        (please read their documentation/code to understand their purposes):

            @classmethod
            _pre_init_(cls)

            @classmethod
            get_ext_appendix(cls, file_name)

            @classmethod
            get_new_file_ext(cls, view, file_name=None)

            new_file_ext(self)

            @classmethod
            load_options(self, view)

            get_options(self)

            @classmethod
            file_is_valid(cls, view, file_name=None)

            is_valid(self)

            load(self, *args, **kwargs)
    """
    name    = ""
    ext     = ""
    comment = ""
    scope   = None
    file_regex = ""
    output_panel_name = "package_dev"

    def __init__(self, window, view, file_path=None, output=None, *args, **kwargs):
        """Mirror the parameters to ``self``, do "init" stuff.
        """
        super(LoaderProto, self).__init__()  # object.__init__ takes no parameters

        self.window = window or view.window() or sublime.active_window()
        self.view = view
        self.file_path = file_path or view.file_name()

        path = os.path.split(self.file_path)[0]
        if isinstance(output, OutputPanel):
            output.set_path(path, self.file_regex)
            self.output = output
        else:
            self.output = OutputPanel(self.window, self.output_panel_name,
                                      file_regex=self.file_regex, path=path)

    @classmethod
    def _pre_init_(cls):
        """Assign attributes that depend on other attributes defined by subclasses.
        """
        if not hasattr(cls, 'ext_regex'):
            cls.ext_regex = r'(?i)\.%s(?:-([^\.]+))?$' % cls.ext

        if not hasattr(cls, 'opt_regex'):
            # Will result in an exception when running cls.load_options but will be caught.
            cls.opt_regex = cls.comment and r'^\s*%s\s+\[PackageDev\]\s+(.+)$' % cls.comment or ""

    @classmethod
    def get_ext_appendix(cls, file_name):
        """Returns the appendix part of a file_name in style ".json-Appendix",
        "json" being ``self.ext`` respectively, or ``None``.
        """
        if file_name:
            ret = re.search(cls.ext_regex, file_name)
            if ret and ret.group(1):
                return ret.group(1)
        return None

    @classmethod
    def get_new_file_ext(cls, view, file_path=None):
        """Returns a tuple in style (str(ext), bool(prepend_ext)).

        The first part is the extension string, which may be ``None``.
        The second part is a boolean value that indicates whether the dumper
        (or the handler) should use the value of the first part as appendix
        and prepend the actual "new" file type.

        See also get_ext_appendix().
        """
        file_path = file_path or view and view.file_name()
        if not file_path:
            return (None, False)

        appendix = cls.get_ext_appendix(file_path)
        if appendix:
            return ('.' + appendix, False)

        ext = os.path.splitext(file_path)[1]
        if not ext == '.' + cls.ext and cls.file_is_valid(view, file_path):
            return (ext, True)

        return (None, False)

    def new_file_ext(self):
        """Instance method wrapper for ``cls.get_new_file_ext``.
        """
        return self.__class__.get_new_file_ext(self.view, self.file_path)

    @classmethod
    def load_options(self, view):
        """Search for a line comment in the first few lines which starts with
        ``"[PackageDev]"`` and parse the following things using ``yaml.safe_load``
        after wrapping them in "{}".
        """
        # Don't bother reading the file to load its options.
        if not view:
            return None

        # Search for options in the first 3 lines (compatible with xml)
        for i in range(3):
            try:
                line = coorded_substr(view, (i, 0), (i, -1))
                optstr = re.search(self.opt_regex, line)
                # Just parse the string with yaml; wrapped in {}
                # Yeah, I'm lazy like that, but see, I even put "safe_" in front of it
                return yaml.safe_load('{%s}' % optstr.group(1))
            except:
                continue

        return None

    def get_options(self):
        """Instance method wrapper for ``cls.load_options``.
        """
        return self.__class__.load_options(self.view)

    @classmethod
    def file_is_valid(cls, view, file_path=None):
        """Returns a boolean whether ``file_path`` is a valid file for
        this loader.
        """
        file_path = file_path or view and view.file_name()
        if not file_path:
            return None

        return (cls.get_ext_appendix(file_path) is not None
                or file_path_tuple(file_path).ext == '.' + cls.ext
                or (cls.scope is not None and view
                    and base_scope(view) == cls.scope))

    def is_valid(self):
        """Instance method wrapper for ``cls.file_is_valid``.
        """
        return self.__class__.file_is_valid(self.view, self.file_path)

    def load(self, *args, **kwargs):
        """Wraps ``self.parse(*args, **kwargs)`` and calls some other functions
        similar for almost every loader.

        This function is called by the handler directly.
        """
        if not self.is_valid():
            self.output.write_line("Not a %s file." % self.name)
            return

        self.output.write_line("Parsing %s... (%s)" % (self.name, self.file_path))

        return self.parse(*args, **kwargs)

    def parse(self, *args, **kwargs):
        """To be implemented. Should return the parsed data from
        ``self.file_path`` as a Python object.
        """
        pass


class JSONLoader(LoaderProto):
    name    = "JSON"
    ext     = "json"
    comment = "//"
    scope   = "source.json"
    debug_base = 'Error parsing ' + name + ' "%s": %s'
    file_regex = debug_base % (r'(.*?)', r'.+? line (\d+) column (\d+)')

    def parse(self, *args, **kwargs):
        text = get_text(self.view)
        try:
            text = strip_js_comments(text)
            data = json.loads(text)
        except ValueError as e:
            self.output.write_line(self.debug_base % (self.file_path, str(e)))
        else:
            return data


class PlistLoader(LoaderProto):
    name = "Property List"
    ext  = "plist"
    debug_base = 'Error parsing ' + name + ' "%s": %s, line %s, column %s'
    file_regex = re.escape(debug_base).replace(r'\%', '%') % (r'(.*?)', r'.*?', r'(\d+)', r'(\d+)')
    opt_regex = r'^\s*<!--\s+\[PackageDev\]\s+(.+)-->'
    DOCTYPE = "<!DOCTYPE plist"

    @classmethod
    def file_is_valid(cls, view, file_path=None):
        file_path = file_path or view and view.file_name()
        if not file_path:
            return None

        if (cls.get_ext_appendix(file_path) is not None
                or os.path.splitext(file_path)[1] == '.' + cls.ext):
            return True

        # Plists have no scope (syntax definition) since they are XML.
        # Instead, check for the DOCTYPE in the first three lines.
        if view:
            for i in range(3):  # This would be a really terrible one-liner
                text = coorded_substr(view, (i, 0), (i, len(cls.DOCTYPE)))
                if text == cls.DOCTYPE:
                    return True
        return False

    def parse(self, *args, **kwargs):
        # Note: I hate Plist and XML. And it doesn't help a bit that parsing
        # plist files is a REAL PITA.
        text = get_text(self.view)

        # Parsing will fail if `<?xml version="1.0" encoding="UTF-8"?>` encoding is in the first
        # line, so strip it.
        # XXX: Find a better way to fix this misbehaviour of xml stuff in Python
        #      (I mean, plistliv even "writes" that line)
        if text.startswith('<?xml version="1.0" encoding="UTF-8"?>'):
            text = text[38:]

        if use_plistlib:
            try:
                # This will try `from xml.parsers.expat import ParserCreate`
                # but since it is already tried above it should succeed.
                data = plistlib.readPlistFromBytes(text.encode('utf-8'))
            except ExpatError as e:
                self.output.write_line(self.debug_base
                                       % (self.file_path,
                                          ErrorString(e.code),
                                          e.lineno,
                                          e.offset)
                                       )
            # except BaseException as e:
            #     # Whatever could happen here ...
            #     self.output.write_line(self.debug_base % (self.file_path, str(e), 0, 0))
            else:
                return data
        else:
            # falling back to plist_parser
            from xml.sax._exceptions import SAXReaderNotAvailable
            try:
                data = plist_parser.parse_string(text)
            except plist_parser.PropertyListParseError as e:
                self.output.write_line(self.debug_base % (self.file_path, str(e), 0, 0))
            except SAXReaderNotAvailable:
                # https://github.com/SublimeText/AAAPackageDev/issues/48
                self.output.write_line("Unable to parse Property List because of missing XML "
                                       "parsers in your Python environment.\n"
                                       "Please use Sublime Text 3 or reinstall Python 2.6 "
                                       "on your system.")
            else:
                return data


class YAMLLoader(LoaderProto):
    name    = "YAML"
    ext     = "yaml"
    comment = "#"
    scope   = "source.yaml"
    debug_base = "Error parsing YAML: %s"
    file_regex = r'^ +in "(.*?)", line (\d+), column (\d+)'

    def parse(self, *args, **kwargs):
        text = get_text(self.view)
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            out = self.debug_base % str(e).replace("<unicode string>", self.file_path)
            self.output.write_line(out)
        except IOError as e:
            self.output.write_line('Error opening "%s": %s' % (self.file_path, str(e)))
        else:
            return data


###############################################################################


# Collect all the loaders and assign them to `get`
get = dict()
for type_name in dir():
    try:
        t = globals()[type_name]
        if t.__bases__:
            if issubclass(t, LoaderProto) and t is not LoaderProto:
                t._pre_init_()
                get[t.ext] = t

    except AttributeError:
        pass
