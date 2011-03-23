import sys
import os

import mock

import sublime


here = os.path.split(__file__)[0]
path_to_lib = os.path.normpath(os.path.join(here, '..', '..', 'Lib'))
if not path_to_lib in sys.path:
    sys.path.append(path_to_lib)


import sublime_lib.view.sel as su_lib_sels


def test_has_sels():
    view = mock.Mock()
    view.sel.return_value = range(1)

    assert su_lib_sels.has_sels(view)