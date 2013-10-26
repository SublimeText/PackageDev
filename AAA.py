import os
import sys

from sublime import packages_path

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

# Makes sublime_lib package available for all packages.
libpath = os.path.join(BASE_PATH, "Lib")
if not libpath in sys.path:
    sys.path.append(libpath)
    print "[AAAPackageDev] Added sublime_lib to sys.path."
