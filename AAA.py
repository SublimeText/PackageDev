import sublime

import os
import sys

# Makes sublime_lib package available for all packages.
libpath = os.path.join(sublime.packages_path(), "AAAPackageDev", "Lib")
if not libpath in sys.path:
    sys.path.append(libpath)
    print "[AAAPackageDev] Added sublime_lib to sys.path."
