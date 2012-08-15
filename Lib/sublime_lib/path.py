import sublime as _sublime
from collections import namedtuple as _namedtuple
import os as _os


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
    return _os.path.join(_sublime.packages_path(), *leafs)


def root_at_data(*leafs):
    """Combines leafs with Sublime's ``Data`` folder.
    """
    data = _os.path.join(_os.path.split(_sublime.packages_path())[0])
    return _os.path.join(data, *leafs)


FilePath = _namedtuple("FilePath", "file_path path file_name base_name ext no_ext")


def file_path_tuple(file_path):
    """Creates a named tuple with the following attributes:
    file_path, path, file_name, base_name, ext, no_ext
    """
    path, file_name = _os.path.split(file_path)
    base_name, ext = _os.path.splitext(file_name)
    return FilePath(
        file_path,
        path,
        file_name,
        base_name,
        ext,
        no_ext=_os.path.join(path, base_name)
    )
