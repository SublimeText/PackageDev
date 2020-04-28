import logging
import os
import uuid

import sublime
import sublime_plugin

from ..lib import syntax_paths
from .templates import TEMPLATES

__all__ = ('PackagedevNewResourceCommand',)

logger = logging.getLogger(__name__)


def _syntax_path_for_kind(kind):
    if kind == 'tm_syntax_def':
        kind = 'plist'
    key = kind.upper()
    return getattr(syntax_paths, key)


def _get_template(kind, suffix):
    template_key = kind
    if suffix:
        template_key = "{}_{}".format(kind, suffix)
    template = TEMPLATES[template_key]

    if template_key.startswith("tm_"):
        # tm_* kinds expect a uuid to be inserted
        template = template % uuid.uuid4()

    return template


def _default_file_name(kind, suffix, package_name):
    name = None
    extension = None
    if kind == 'tm_syntax_def':  # only syntax with multiple extensions (plist)
        extension = ".tmLanguage"
    elif (kind, suffix) == ('menu', 'main'):
        name = "Main"
    elif kind.endswith("map"):
        name = "Default"
    elif kind in ('commands', 'settings', 'build_system'):
        name = package_name

    return name, extension


class PackagedevNewResourceCommand(sublime_plugin.WindowCommand):

    """Command to create a new resource file.

    - Assigns the proper syntax.
    - Sets the default directory to the current project folder, if it is a package.
    - Prefills package name in snippets, if possible.
    """

    def run(self, kind, suffix=None):
        if kind not in TEMPLATES:
            logger.error("Unknown resource file kind %r", kind)
            return

        package_dir = self._guess_folder()
        package_name = self._guess_package_name(package_dir)
        logger.debug("Guessed package name %r from path %r", package_name, package_dir)

        v = self.window.new_file()

        # initialize settings (and syntax)
        v.set_syntax_file(_syntax_path_for_kind(kind))
        v.settings().set('default_dir', package_dir)
        name, extension = _default_file_name(kind, suffix, package_name)
        if name:
            v.set_name(name)
        if extension:
            v.settings().set('default_extension', extension)

        # insert the template
        snippet_args = {'contents': _get_template(kind, suffix)}
        # prefill snippet with package name
        if package_name:
            snippet_args["package_name"] = package_name

        v.run_command('insert_snippet', snippet_args)

    def _guess_package_name(self, path=None):
        """Determine the package name currently being edited, or None."""
        path = path or self._guess_folder()
        name = os.path.basename(path)
        return name if name != "User" else None

    def _guess_folder(self):
        """Return the path to either the package currently being edited, or User."""
        folders = self.window.folders()
        # Test if the first folder is a package
        if len(folders) >= 1:
            if self._is_package_path(folders[0]):
                return folders[0]
        return os.path.join(sublime.packages_path(), "User")

    def _is_package_path(self, file_path):
        """Test if file_path points to a ST package (while resolving symlinks).

        Resolves symlinks for both the packages path and the argument.
        """
        if not file_path:
            return False

        packages_path = sublime.packages_path()
        real_packages_path = os.path.realpath(packages_path)
        real_file_path = os.path.realpath(file_path)

        for pp in (real_packages_path, packages_path):
            for fp in (real_file_path, file_path):
                if fp.startswith(pp):
                    leaf = fp[len(pp):].strip(os.sep)
                    return (os.sep not in leaf)
