from collections import OrderedDict
import inspect
import functools
import logging
import yaml

import sublime
import sublime_plugin

from .yaml_omap import SaveOmapLoader

BUILTIN_METADATA_FILENAME = "builtin_commands_meta_data.yaml"

l = logging.getLogger(__name__)


def get_command_name(command_class):
    """Get the name of a command.

    Parameters:
        command_class (sublime_plugin.Command)
            The command class for which the name should be retrieved.

    Returns (str)
        The name of the command.
    """
    # Copy of the `sublime_plugin.Command.name` method.
    # Don't initialize the class and call its method,
    # because virtually nobody overwrites it anyway.
    clsname = command_class.__name__
    name = clsname[0].lower()
    last_upper = False
    for c in clsname[1:]:
        if c.isupper() and not last_upper:
            name += '_'
            name += c.lower()
        else:
            name += c
        last_upper = c.isupper()
    if name.endswith("_command"):
        name = name[0:-8]
    return name


@functools.lru_cache()
def get_builtin_command_meta_data():
    """Retrieve the meta data of built-in commands.

    The result is cached after the first call.

    Returns (dict)
        The stored meta data for each command, keyed by their names.
    """
    l.debug("Loading built-in command meta data")

    res_paths = sublime.find_resources(BUILTIN_METADATA_FILENAME)
    result = {}
    for res_path in res_paths:
        try:
            res_raw = sublime.load_resource(res_path)
            res_content = yaml.load(res_raw, Loader=SaveOmapLoader)
        except (OSError, ValueError) as e:
            l.exception("couldn't load resource: %s", res_path)
        else:
            result.update(res_content)

    return result


@functools.lru_cache()
def get_builtin_commands(command_type=""):
    """Retrieve a set of the names of the built-in commands.

    Results are cached.

    Parameters:
        command_type (str) = ""
            Limit the commands to the given type.
            Valid types are "" to get all types, "text", "window", and "app".

    Returns (frozenset of str)
        The command names for the type.
    """
    meta = get_builtin_command_meta_data()
    if not command_type:
        result = frozenset(meta.keys())
    else:
        result = frozenset(k for k, v in meta.items()
                           if v['command_type'] == command_type)

    for c in iter_python_command_classes(command_type):
        name = get_command_name(c)
        module = c.__module__
        package = module.split(".")[0]
        if package == 'Default':
            if name in result:
                l.warning(
                    'command "{name}" in the {package} package is defined in the built-in '
                    'metadata file, probably it should not be'.format(name=name, package=package)
                )

    return result


def iter_python_command_classes(command_type=""):
    """Iterate over all commands for a given command type.

    Parameters:
        command_type (str) = ""
            Limit the commands to the given type.
            Valid types are "" to get all types, "text", "window", and "app".

    Returns (list of sublime_plugin.Command)
        The command classes for the command type.
    """
    if not command_type:
        for cmd_list in sublime_plugin.all_command_classes:
            yield from iter(cmd_list)
    else:
        cmd_list = {
            "text": sublime_plugin.text_command_classes,
            "window": sublime_plugin.window_command_classes,
            "app": sublime_plugin.application_command_classes
        }[command_type]
        yield from iter(cmd_list)


def extract_command_class_args(command_class):
    """
    Extract the run arguments from a command class.

    Parameters:
        command_class (sublime_plugin.Command)
            The command class, which should be used to extract the
            arguments.

    Returns (dict with arg mapping)
        Maps arguments to their default value (or None).
    """
    spec = inspect.getfullargspec(command_class.run)
    args = spec.args
    defaults = spec.defaults or ()
    num_non_default_args = len(args) - len(defaults)
    l.debug("Args for command %r: %s; defaults: %s",
            get_command_name(command_class), args, defaults)

    arg_dict = OrderedDict()
    for i, arg in enumerate(args):
        if i == 0:  # strip 'self' arg
            continue
        elif i == 1 and issubclass(command_class, sublime_plugin.TextCommand):  # and 'edit'
            if arg != "edit":
                l.warning("Second argument for TextCommand is not named 'edit'. Ignoring anyway")
            continue
        elif i < num_non_default_args:
            value = None
        else:
            value = defaults[i - num_non_default_args]
        arg_dict[arg] = value

    return arg_dict


def find_class_from_command_name(command_name):
    """Find the Python class for a specific command name.

    Parameters:
        command_name (str)
            The command name, which should be used to find the class.

    Returns (sublime_plugin.Command)
        The python class, which belongs to the command name, or None.
    """
    return next(
        (c for c in iter_python_command_classes()
         if get_command_name(c) == command_name),
        None
    )


def get_args_from_command_name(command_name):
    """Extract or fetch arguments from a built-in command or command class, by name.

    Parameters:
        command_name (str)
            The command name, which should be used to find the class,
            which should be used to extract the arguments.

    Returns (dict with arg mapping)
        Maps arguments to their default value (or None).
    """
    builtin_meta_data = get_builtin_command_meta_data()
    if command_name in builtin_meta_data:
        return builtin_meta_data[command_name].get("args", {})
    else:
        command_class = find_class_from_command_name(command_name)
        if command_class:
            return extract_command_class_args(command_class)
        else:
            return None  # the command is not defined
