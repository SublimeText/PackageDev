import datetime

import json
import yaml
import plistlib

from sublime_lib.view import OutputPanel


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
                Defaults to ``"aaa_package_dev"``.


        Methods to be implemented:

            write(self, data, *args, **kwargs)
                This is called when the actual parsing should happen.

                Data to write is defined in ``data``.
                The parsed data should be returned.
                To output problems, use ``self.output.write_line(str)``.
                The default self.dump function will catch excetions raised
                and print them via ``str()`` to the output.

                *args, **kwargs parameters are passed from
                ``load(self, *args, **kwargs)``. If you want to specify or
                process any options or optional parsing, use these.

            validate_data(self, data, *args, **kwargs) (optional)

                Called by self.dump. Please read the documentation for
                _validate_data in order to understand how this function works.

        Methods you can override/implement
        (please read their documentation/code to understand their purposes):

            _validate_data(self, data, funcs)

            dump(self, *args, **kwargs)
    """
    name = ""
    ext  = ""
    output_panel_name = "aaa_package_dev"

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
        """
        # Some _validate_data call
        pass

    def _validate_data(self, data, funcs):
        """Check for incompatible data recursively.

        ``funcs`` is supposed to be a set, or just iterable two times and
        represents two functions, one to test whether the data is invalid
        and one to validate it. Both functions accept one parameter:
        the object to test.

        Example:
            funcs = ((lamda x: isinstance(x, int), int)
                     (lamda x: isinstance(x, str), str))
        """
        checked = []

        def check_recursive(obj):
            for is_invalid, validate in funcs:
                if is_invalid(obj):
                    obj = validate(obj)
            if obj in checked:
                return
            if isinstance(obj, list) or isinstance(obj, dict):
                for sub_obj in obj:
                    checked.append(sub_obj)
                    check_recursive(sub_obj)

        check_recursive(data)
        return data

    def dump(self, data, *args, **kwargs):
        """Wraps the ``self.write`` function.

        This function is called by the handler directly.
        """
        self.output.write_line("Writing %s... (%s)" % (self.name, self.new_file_path))
        self.output.show()
        self.validate_data(data)
        try:
            self.write(data, *args, **kwargs)
        except Exception, e:
            self.output.write_line("Error writing json: %s" % str(e))

    def write(self, data, *args, **kwargs):
        """To be implemented.
        """
        pass


class JSONDumper(DumperProto):
    name = "JSON"
    ext  = "json"

    def validate_data(self, data):
        self._validate_data(data, [
            (lambda x: isinstance(x, datetime.date), str)  # TOTEST # from yaml
            (lambda x: isinstance(x, datetime.datetime), str)  # TOTEST # from plist and yaml
        ])

    def write(self, data, *args, **kwargs):
        # Define default parameters
        json_params = dict(
                           skipkeys=True,
                           check_circular=False,  # there won't be references here, hopefully
                           indent=4,
                           sort_keys=True
                          )
        json_params.update(kwargs)

        with open(self.new_file_path, "w") as f:
            json.dump(data, f, **json_params)


class PlistDumper(DumperProto):
    name = "Property List"
    ext  = "plist"

    def validate_data(self, data):
        self._validate_data(data, [
            (lambda x: isinstance(x, datetime.date), str)  # TOTEST
        ])

    def write(self, data):
        plistlib.writePlist(data, self.new_file_path)


class YAMLDumper(DumperProto):
    name = "YAML"
    ext  = "yaml"

    def write(self, data):
        with open(self.new_file_path, "w") as f:
            yaml.safe_dump(data, f)


###############################################################################


# Collect all the dumpers and assign them to `get`
get = dict()
for type_name in dir():
    try:
        t = globals()[type_name]
        if t.__bases__:
            is_plugin = False
            if issubclass(t, DumperProto) and not t is DumperProto:
                get[t.ext] = t

    except AttributeError:
        pass
