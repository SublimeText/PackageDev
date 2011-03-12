import sys
import os

import mock

import sublime


here = os.path.split(__file__)[0]
path_to_lib = os.path.normpath(os.path.join(here, "..", "..", "Lib"))
if not path_to_lib in sys.path:
    sys.path.append(path_to_lib)


import sublime_lib.path as su_path


def test_root_at_packages():
    sublime.packages_path = mock.Mock()
    sublime.packages_path.return_value = "XXX"
    expected = os.path.join("XXX", "ZZZ")
    assert su_path.root_at_packages("ZZZ") == expected