import sys
import os

import mock

import sublime

import sublime_lib.view as su_lib_view


def test_has_file_ext():
    view = mock.Mock()

    view.file_name.return_value = "foo.bar"
    assert su_lib_view.has_file_ext(view, "bar")

    view.file_name.return_value = 'foo.'
    assert not su_lib_view.has_file_ext(view, ".")

    view.file_name.return_value = ''
    assert not su_lib_view.has_file_ext(view, ".")

    view.file_name.return_value = ''
    assert not su_lib_view.has_file_ext(view, '')    

    view.file_name.return_value = 'foo'
    assert not su_lib_view.has_file_ext(view, '')

    view.file_name.return_value = 'foo'
    assert not su_lib_view.has_file_ext(view, 'foo')

    view.file_name.return_value = None
    assert not su_lib_view.has_file_ext(view, None)

    view.file_name.return_value = None
    assert not su_lib_view.has_file_ext(view, '.any')


def test_has_sels():
    view = mock.Mock()
    view.sel.return_value = range(1)

    assert su_lib_view.has_sels(view)