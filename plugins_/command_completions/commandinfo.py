import inspect
import functools
import logging
import yaml

import sublime
import sublime_plugin

l = logging.getLogger(__name__)


def get_command_name(command_class):
    """
    Get the name of a command.

    Parameters:
        command_class (<:sublime_plugin.Command)
            The command class for which the name should be retrieved.


    Returns (str)
        The name of the command.
    """
    # Copy of the default name() method
    # Don't initialize the class and call the method there, because
    # nobody overwrites the method anyway.
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
    """
    Retrieve the meta data of the built-in commands.

    The result is cached after the first call.

    Returns (dict)
        The stored meta data for each command accessible by their names.
    """
    l.debug("Loading built-in command meta data")

    res_paths = sublime.find_resources(
        "sublime_text_builtin_commands_meta_data.yaml")
    result = {}
    for res_path in res_paths:
        try:
            res_raw = sublime.load_resource(res_path)
            res_content = yaml.load(res_raw)
        except (OSError, ValueError) as e:
            l.error("couldn't load resource: %s; %s%s",
                    res_path, e.__class__.__name__, e.args)
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
        command_class (<:sublime_plugin.Command)
            The command class, which should be used to extract the
            arguments.


    Returns (list of tuples)
        The arguments with their default value. Each entry is either a
        tuple with length 1 or 2. If it has the length 1 it doesn't
        have a default value. Otherwise the second entry is the default
        value.
    """
    spec = inspect.getfullargspec(command_class.run)
    args = spec.args
    defaults = list(reversed(spec.defaults or []))
    command_args = list(reversed([
        (a, defaults[i]) if len(defaults) > i else (a,)
        for i, a in enumerate(reversed(args))
    ]))
    # strip given arguments (self and edit)
    if issubclass(command_class, sublime_plugin.TextCommand):
        command_args = command_args[2:]
    else:
        command_args = command_args[1:]
    return command_args


def find_class_from_command_name(command_name):
    """
    Returns the python class for a specific command name.

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
    """
    Extract the run arguments from a command class, which belongs to a
    command name.

    Parameters:
        command_name (str)
            The command name, which should be used to find the class,
            which should be used to extract the arguments.


    Returns (list of tuples)
        The arguments with their default value. Each entry is either a
        tuple with length 1 or 2. If it has the length 1 it doesn't
        have a default value. Otherwise the second entry is the default
        value.
    """
    builtin_meta_data = get_builtin_command_meta_data()
    if command_name in builtin_meta_data:
        # check whether it is in the builtin command list
        command_args = builtin_meta_data[command_name].get("args", [])
    else:
        command_class = find_class_from_command_name(command_name)
        if not command_class:
            return  # the command is not defined
        command_args = extract_command_class_args(command_class)
    return command_args
