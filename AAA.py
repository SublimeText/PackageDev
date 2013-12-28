import os
import sys

from sublime import packages_path

PLUGIN_NAME = os.getcwd().replace(packages_path(), '')[1:]

# Makes sublime_lib package available for all packages.
libpath = os.path.join(packages_path(), PLUGIN_NAME, "Lib")
if not libpath in sys.path:
    sys.path.append(libpath)
    print("[AAAPackageDev] Added sublime_lib to sys.path.")
