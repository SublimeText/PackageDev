# import ST-interfacing classes from sub-modules

from .command_completions import *  # noqa
from .file_conversion import *  # noqa
from .new_resource_file import *  # noqa
from .settings import *  # noqa
from .snippet_dev import *  # noqa
from .syntax_dev import *  # noqa
from .syntax_dev_legacy import *  # noqa
from .syntaxtest_dev import *  # noqa

from . import xml_hidden_extensions_hotfix


def plugin_loaded():
    xml_hidden_extensions_hotfix.plugin_loaded()


def _is_plugin_class(obj):
    if not hasattr(obj, '__bases__'):
        return False

    for base in obj.__bases__:
        if base.__module__ == 'sublime_plugin':
            return True


def _check_missing():
    """Can be invoked manually to ensure we didn't miss a plugin class.

    Only works outside of a .sublime-package file.

    from PackageDev.plugins_ import _check_missing; _check_missing()
    """
    import os
    import importlib

    plugin_classes = []
    special_callbacks = {'plugin_loaded': [], 'plugin_unloaded': []}

    # collect all plugin sub-classes in this folder
    folder = os.path.dirname(__file__)
    names = os.listdir(folder)
    for name in names:
        if name == "__init__.py":
            continue
        path = os.path.join(folder, name)
        mod_name, ext = os.path.splitext(name)
        if name == "lib" or os.path.isfile(path) and ext != ".py":
            continue

        module = importlib.import_module("." + mod_name, __package__)

        for k, v in module.__dict__.items():
            if k in special_callbacks:
                special_callbacks[k].append(v)
            elif _is_plugin_class(v):
                plugin_classes.append(v)

    print("found {} plugin classes".format(len(plugin_classes)))
    print("special callbacks: {}".format(special_callbacks))

    # assert that every item in plugin_classes is also in globals()
    imported = globals().values()
    for plugin in plugin_classes:
        if plugin not in imported:
            print("[!!] plugin missing: {p.__module__}.{p.__qualname__} ({p})".format(p=plugin))
