import sublime

import os


def root_at_packages(*leafs):
    """Combines leafs with path to Sublime's Packages folder.
    """
    return os.path.join(sublime.packages_path(), *leafs)