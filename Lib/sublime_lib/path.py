import sublime

import os


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
    return os.path.join(sublime.packages_path(), *leafs)


def root_at_data(*leafs):
    """Combines leafs with Sublime's ``Data`` folder.
    """
    data = os.path.join(os.path.split(sublime.packages_path())[0])
    return os.path.join(data, *leafs)


def path_to_dict(file_path):
    """Returns a dict with the following fields:
    file_path, path, file_name, ext, no_ext
    """
    path, file_name = os.path.split(file_path)
    base_name, ext = os.path.splitext(file_name)
    return dict(
        file_path=file_path,
        path=path,
        file_name=file_name,
        ext=ext,
        no_ext=os.path.join(path, base_name)
    )
