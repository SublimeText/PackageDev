import os
import sys

libpath = os.path.join(os.path.dirname(__file__), "Lib")
if sys.version_info[0] == 3:
    sys.path.append(os.path.join(libpath, 'py3'))
    from collections import OrderedDict
    string_types = str,
else:
    sys.path.append(os.path.join(libpath, 'py2'))
    from ordereddict import OrderedDict
    string_types = basestring,
