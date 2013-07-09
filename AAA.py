import os
import sys
import sublime


# Makes sublime_lib package available for all packages.
here = os.path.split(__file__)[0]
path_to_lib = os.path.normpath(os.path.join(here, "Lib"))
if not path_to_lib in sys.path:
    sys.path.append(path_to_lib)
    print("[AAAPackageDev] Added %s to sys.path." % path_to_lib)
