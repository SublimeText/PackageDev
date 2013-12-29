import os
import sys

# Makes sublime_lib package available for all packages.
PLUGIN_DIR = os.path.abspath(os.path.dirname(__file__))
PLUGIN_NAME = os.path.split(PLUGIN_DIR)[1]

libpaths = [
    os.path.join(PLUGIN_DIR, "Lib"),
    # The current package is not imported as a python module in sublime text 2, so add the import path and use absolute imports.
    os.path.dirname(PLUGIN_DIR)
]
for libpath in libpaths:
    if not libpath in sys.path:
        sys.path.append(libpath)
        print("[AAAPackageDev] Added {0} to sys.path.".format(libpath))
