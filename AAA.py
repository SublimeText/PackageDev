import os
import sys

try:  # ST3
    from .Lib.sublime_lib.path import get_package_name

    PLUGIN_NAME = get_package_name()
    path = os.path.dirname(__file__)
    libpath = os.path.join(path, "Lib")
except ValueError:  # ST2
    # For some reason the import does only work when RELOADING the plugin, not
    # when ST is loading it initially.

    # from lib.sublime_lib.path import get_package_name, get_package_path
    path = os.path.normpath(os.getcwdu())
    PLUGIN_NAME = os.path.basename(path)
    libpath = os.path.join(path, "Lib")


def add(path):
    if not path in sys.path:
        sys.path.append(path)
        print("[%s] Added %s to sys.path." % (PLUGIN_NAME, path))

# Make sublime_lib (and more) available for all packages.
add(libpath)
# Differentiate between Python 2 and Python 3 packages (split by folder)
add(os.path.join(libpath, "_py%d" % sys.version_info[0]))
