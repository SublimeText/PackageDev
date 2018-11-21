import datetime

import json
import yaml
import plistlib

from sublime_lib import OutputPanel


class DumperProto(object):
    """Prototype class for data dumpers of different types.

        Classes derived from this class (and in this file) will be appended
        to the module's ``get`` variable (a dict) with ``self.ext`` as their key.

        Variables to be defined:

            name (str)
                The dumpers name, e.g. "JSON" or "Property List".

            ext (str)
                The default file extension.

            output_panel_name (str; optional)
                If this is specified it will be used as the output panel's
                reference name.
                Defaults to ``"package_dev"``.

            default_params (dict; optional)
                Just a dict of the default params for self.write().

            allowed_params (set/tuple; optional)
                A collection of strings defining the allowed parameters for
                self.write(). Other keys in the kwargs dict will be removed.


        Methods to be implemented:

            write(self, data, params, *args, **kwargs)
                This is called when the actual parsing should happen.

                Data to write is defined in ``data``.
                The parsed data should be returned.
                To output problems, use ``self.output.print(str)``.
                The default self.dump function will catch excetions raised
                and print them via ``str()`` to the output.

                Parameters to the dumping functions are in ``params`` dict,
                which have been validated before, according to the class
                variables (see above).
                *args, **kwargs parameters are passed from
                ``load(self, *args, **kwargs)``. If you want to specify or
                process any options or optional parsing, use these.

            validate_data(self, data, *args, **kwargs) (optional)

                Called by self.dump. Please read the documentation for
                _validate_data in order to understand how this function works.

        Methods you can override/implement
        (please read their documentation/code to understand their purposes):

            _validate_data(self, data, funcs)

            validate_params(self, params)

            dump(self, *args, **kwargs)
    """
    name = ""
    ext  = ""
    output_panel_name = "package_dev"
    default_params = {}
    allowed_params = ()

    def __init__(self, window, view, new_file_path, output=None, file_path=None, *args, **kwargs):
        """Guess what this does.
        """
        self.window = window
        self.view = view
        self.file_path = file_path or view.file_name()
        self.new_file_path = new_file_path

        if isinstance(output, OutputPanel):
            self.output = output
        elif window:
            self.output = OutputPanel(window, self.output_panel_name)

    def validate_data(self, data, *args, **kwargs):
        """To be implemented (optional).

            Must return the validated data object.

            Example:
                return self._validate_data(data, [
                    ((lambda x: isinstance(x, float), int),
                     (lambda x: isinstance(x, datetime.datetime), str),
                     (lambda x: x is None, False))
                ]
        """
        pass

    def _validate_data(self, data, funcs):
        """Check for incompatible data recursively.

        ``funcs`` is supposed to be a set, or just iterable two times and
        represents two functions, one to test whether the data is invalid
        and one to validate it. Both functions accept one parameter:
        the object to test.
        The validation value can be a function (is callable) or be a value.
        In the latter case the value will always be used instead of the
        previous object.

        Example:
            funcs = ((lambda x: isinstance(x, float), int),
                     (lambda x: isinstance(x, datetime.datetime), str),
                     (lambda x: x is None, False))
        """
        checked = []

        def check_recursive(obj):
            # won't and shouldn't work for immutable types
            # I mean, why would you even reference objects inside themselves?
            if obj in checked:
                return obj
            checked.append(obj)

            for is_invalid, validate in funcs:
                if is_invalid(obj):
                    if callable(validate):
                        obj = validate(obj)
                    else:
                        obj = validate

            if isinstance(obj, dict):  # dicts are fine
                for key in obj:
                    obj[key] = check_recursive(obj[key])

            if isinstance(obj, list):  # lists are too
                for i in range(len(obj)):
                    obj[i] = check_recursive(obj[i])

            if isinstance(obj, tuple):  # tuples are immutable ...
                return tuple([check_recursive(sub_obj) for sub_obj in obj])

            if isinstance(obj, set):  # sets ...
                for val in obj:
                    new_val = check_recursive(val)
                    if new_val != val:  # a set's components are hashable, no need to "is"
                        obj.remove(val)
                        obj.add(new_val)

            return obj

        return check_recursive(data)

    def validate_params(self, params):
        """Validate the parameters according to self.default_params and
        self.allowed_params.
        """
        new_params = self.default_params.copy()
        new_params.update(params)
        for key in params.keys():
            if key not in self.allowed_params:
                del new_params[key]
        return new_params

    def dump(self, data, *args, **kwargs):
        """Wraps the ``self.write`` function.

        This function is called by the handler directly.
        """
        self.output.print("Writing %s... (%s)" % (self.name, self.new_file_path))
        self.output.show()
        data = self.validate_data(data)
        params = self.validate_params(kwargs)

        self.write(data, params, *args, **kwargs)

    def write(self, data, *args, **kwargs):
        """To be implemented."""
        pass


class JSONDumper(DumperProto):
    name = "JSON"
    ext  = "json"
    default_params = dict(
        skipkeys=True,
        check_circular=False,  # there won't be references here, hopefully
        indent=4
    )
    allowed_params = (
        'skipkeys',
        'ensure_ascii',
        'check_circular',
        'allow_nan',
        'sort_keys',
        'indent',
        'separators',
        'encoding'
    )

    def validate_data(self, data):
        return self._validate_data(data, (
            # TOTEST: sets
            (lambda x: isinstance(x, plistlib.Data), lambda x: x.data),  # plist
            (lambda x: isinstance(x, datetime.date), str),  # yaml
            (lambda x: isinstance(x, datetime.datetime), str)  # plist and yaml
        ))

    def write(self, data, params, *args, **kwargs):
        """Parameters:

            skipkeys (bool)
                Default: True

                Dict keys that are not of a basic type (str, unicode, int,
                long, float, bool, None) will be skipped instead of raising a
                TypeError.

            ensure_ascii (bool)
                Default: True

                If False, then some chunks may be unicode instances, subject to
                normal Python str to unicode coercion rules.

            check_circular (bool)
                Default: False

                If False, the circular reference check for container types will
                be skipped and a circular reference will result in an
                OverflowError (or worse).
                Since we are working with file data here this is likely not
                going to happen.

            allow_nan (bool)
                Default: True

                If False, it will be a ValueError to serialize out of range
                float values (nan, inf, -inf) in strict compliance of the JSON
                specification, instead of using the JavaScript equivalents
                (NaN, Infinity, -Infinity).

            sort_keys (bool)
                Default: True

                The output of dictionaries will be sorted by key.

            indent (int)
                Default: 4

                If a non-negative integer, then JSON array elements and object
                members will be pretty-printed with that indent level. An
                indent level of 0 will only insert newlines. None (the default)
                selects the most compact representation.

            separators (tuple, iterable)
                Default: (', ', ': ')

                (item_separator, dict_separator) tuple. (',', ':') is the most
                compact JSON representation.

            encoding (str)
                Default: UTF-8

                Character encoding for str instances, default is UTF-8.
        """
        with open(self.new_file_path, "w") as f:
            json.dump(data, f, **params)


class PlistDumper(DumperProto):
    name = "Property List"
    ext  = "plist"

    def validate_data(self, data):
        return self._validate_data(data, (
            # TOTEST: sets
            # yaml; lost of "precision" when converting to datetime.datetime
            (lambda x: isinstance(x, datetime.date), str),
            (lambda x: x is None, False)
        ))

    def write(self, data, params, *args, **kwargs):
        plistlib.writePlist(data, self.new_file_path)


class YAMLDumper(DumperProto):
    name = "YAML"
    ext  = "yaml"
    default_params = dict(Dumper=yaml.SafeDumper)
    allowed_params = (
        'default_style',
        'default_flow_style',
        'canonical',
        'indent',
        'width',
        'allow_unicode',
        'line_break',
        'encoding',
        'explicit_start',
        'explicit_end',
        'version',
        'tags',
        'Dumper'
    )

    def validate_data(self, data):
        return self._validate_data(data, (
            (lambda x: isinstance(x, plistlib.Data), lambda x: x.data),  # plist
        ))

    def write(self, data, params, *args, **kwargs):
        """Parameters:

            default_style (str)
                Default: None
                Accepted: None, '', '\'', '"', '|', '>'.

                Indicates the style of the scalar.

            default_flow_style (bool)
                Default: True

                Indicates if a collection is block or flow.

            canonical (bool)
                Default: None (-> False)

                Export tag type to the output file.

            indent (int)
                Default: 2
                Accepted: 1 < x < 10

            width (int)
                Default: 80
                Accepted: > indent*2

            allow_unicode (bool)
                Default: None (-> False)

            line_break (str)
                Default: "\n"
                Accepted: u'\r', u'\n', u'\r\n'

            encoding (str)
                Default: 'utf-8'

            explicit_start (bool)
                Default: None (-> False)

                Explicit '---' at the start.

            explicit_end (bool)
                Default: None (-> False)

                Excplicit '...' at the end.

            version (tuple)
                Default: Newest

                Version of the YAML parser: tuple(major, minor).
                Supports only major version 1.

            tags (str?)
                Default: None

                ???

            ===========================

            Dumper (supposedly derived from yaml.BaseDumper)
                You should know what you are doing when passing this.
        """
        with open(self.new_file_path, "w") as f:
            yaml.dump(data, f, **params)


# Add the internal plistlib dict wrapper to the safe dumper
if hasattr(plistlib, '_InternalDict'):
    yaml.SafeDumper.add_representer(
        plistlib._InternalDict,
        yaml.SafeDumper.represent_dict
    )


###############################################################################


# Collect all the dumpers and assign them to `get`
get = dict()
for type_name in dir():
    try:
        t = globals()[type_name]
        if t.__bases__:
            if issubclass(t, DumperProto) and t is not DumperProto:
                get[t.ext] = t

    except AttributeError:
        pass
