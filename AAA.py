import os
import sys

# Makes sublime_lib package available for all packages.
dirname = os.path.abspath(os.path.dirname(__file__))
libpaths = [
    os.path.join(dirname, "Lib"),
    # The current package is not imported as a python module in sublime text 2, so add the import path and use absolute imports.
    os.path.dirname(dirname)
]
for libpath in libpaths:
    if not libpath in sys.path:
        sys.path.append(libpath)
        print("[AAAPackageDev] Added {0} to sys.path.".format(libpath))

# Import compatibility fixes.
import AAAPackageDev.py_compat

# Import any submodule commands so they get loaded.
from sublime_lib.view import *
