import os
import re
import inspect
from collections import namedtuple

import sublime

__all__ = [
    "FTYPE_EXT_KEYMAP",
    "FTYPE_EXT_COMPLETIONS",
    "FTYPE_EXT_SNIPPET",
    "FTYPE_EXT_BUILD",
    "FTYPE_EXT_SETTINGS",
    "FTYPE_EXT_TMPREFERENCES",
    "FTYPE_EXT_TMLANGUAGE",
    "root_at_packages",
    "data_path",
    "root_at_data",
    "file_path_tuple",
    "get_module_path",
    "get_package_name"
]


FTYPE_EXT_KEYMAP        = ".sublime-keymap"
FTYPE_EXT_COMPLETIONS   = ".sublime-completions"
FTYPE_EXT_SNIPPET       = ".sublime-snippet"
FTYPE_EXT_BUILD         = ".sublime-build"
FTYPE_EXT_SETTINGS      = ".sublime-settings"
FTYPE_EXT_TMPREFERENCES = ".tmPreferences"
FTYPE_EXT_TMLANGUAGE    = ".tmLanguage"


def root_at_packages(*leafs):
    """Combines leafs with path to Sublime's Packages folder.
    """
    # If we really need to, we dan extract the packages path from sys.path (ST3)
    return os.path.join(sublime.packages_path(), *leafs)


def data_path():
    """Extract Sublime Text's data path from the packages path.
    Requires the API to finish loading on ST3.
    """
    return os.path.split(sublime.packages_path())[0]


def root_at_data(*leafs):
    """Combines leafs with Sublime's ``Data`` folder.
    """
    data = os.path.join(os.path.dirname(sublime.packages_path()))
    return os.path.join(data, *leafs)


FilePath = namedtuple("FilePath", "file_path path file_name base_name ext no_ext")


def file_path_tuple(file_path):
    """Creates a named tuple with the following attributes:
    file_path, path, file_name, base_name, ext, no_ext
    """
    path, file_name = os.path.split(file_path)
    base_name, ext = os.path.splitext(file_name)
    return FilePath(
        file_path,
        path,
        file_name,
        base_name,
        ext,
        no_ext=os.path.join(path, base_name)
    )


def get_module_path(_file_=None):
    """Returns a tuple with the normalized module path plus a boolean.

    * _file_ (optional)
        The value of `__file__` in your module.
        If omitted, `get_caller_frame()` will be used instead which usually works.

    Returns: (normalized_module_path, archived)
        `normalized_module_path`
            What you usually refer to when using Sublime API, without `.sublime-package`
        `archived`
            True, when in an archive
    """
    if _file_ is None:
        _file_ = get_caller_frame().f_globals['__file__']

    dir_name = os.path.dirname(os.path.abspath(_file_))
    # Check if we are in an archived package
    if not dir_name.endswith(".sublime-package"):
        return dir_name, False

    # We are in a .sublime-package and need to normalize the path
    virtual_path = re.sub(r"(?:Installed )?Packages([\\/][^\\/]+)\.sublime-package(?=[\\/]|$)",
                          r"Packages\1", dir_name)
    return virtual_path, True


def get_package_path(_file_=None):
    """Returns the path to the current Sublime Text package.
    Parameters are the same as for `get_module_path`.
    """
    if _file_ is None:
        _file_ = get_caller_frame().f_globals['__file__']

    mpath = get_module_path(_file_)[0]

    # There probably is a better way for this, but it works
    while not os.path.dirname(mpath).endswith('Packages'):
        if len(mpath) <= 3:
            return None
        # We're not in a top-level plugin.
        # If this was ST2 we could easily use sublime.packages_path(), but ...
        mpath = os.path.dirname(mpath)

    return mpath


def get_package_name(_file_=None):
    """`return os.path.split(get_package_path(_file_))[1]`
    """
    if _file_ is None:
        _file_ = get_caller_frame().f_globals['__file__']

    return os.path.split(get_package_path(_file_))[1]


def get_caller_frame(i=1):
    """Utilizes the inspect module to get the caller's frame.
    You can adjust `i` to find the i-th caller, default is 1.
    """
    # We can't use inspect.stack()[1 + i][1] for the file name because ST sets
    # that to a different value when inside a zip archive.
    return inspect.stack()[1 + i][0]
