import sys
import os

import mock

import sublime


here = os.path.split(__file__)[0]
path_to_lib = os.path.normpath(os.path.join(here, "..", "..", "Lib"))
if not path_to_lib in sys.path:
    sys.path.append(path_to_lib)


import sublime_lib.view as su_lib_view


def test_has_file_extension():
    view = mock.Mock()

    view.file_name.return_value = "xxx.zzz"
    assert su_lib_view.has_file_extension(view, "zzz")

    view.file_name.return_value = 'foo.'
    assert not su_lib_view.has_file_extension(view, ".")

    view.file_name.return_value = ''
    assert not su_lib_view.has_file_extension(view, ".")    