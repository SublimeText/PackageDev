import logging
import os
import uuid

import sublime
import sublime_plugin

from ..lib import syntax_paths
from .templates import TEMPLATES

__all__ = ('NewResourceFileCommand',)

l = logging.getLogger(__name__)


def _syntax_path_for_kind(kind):
    if kind == "tm_syntax_def":
        kind = "plist"
    key = kind.upper()
    return getattr(syntax_paths, key)


class NewResourceFileCommand(sublime_plugin.WindowCommand):

    """Command to create a new resource file.

    - Assigns the proper syntax.
    - Sets the default directory to the current project folder, if it is a package.
    - Prefills package name in snippets, if possible.
    """

    def run(self, kind, default=False):
        if kind not in TEMPLATES:
            l.error("Unknown resource file kind %r", kind)
            return

        v = self.window.new_file()

        # initialize settings (and syntax)
        v.set_syntax_file(_syntax_path_for_kind(kind))
        v.settings().set('default_dir', self._guess_folder())
        if kind == "tm_syntax_def":
            v.settings().set('default_extension', ".tmLanguage")

        # insert the template
        template_key = kind + ("_default" if default else "")
        template = TEMPLATES[template_key]
        if template_key.startswith("tm_"):
            # tm_* kinds expect a uuid to be inserted
            template = template % uuid.uuid4()

        snippet_args = {'contents': template}
        # Prefill snippet with package name, if desired
        if default:
            pkg_name = self._guess_package_name()
            if pkg_name:
                snippet_args["1"] = pkg_name

        v.run_command('insert_snippet', snippet_args)

    def _guess_package_name(self):
        """Determine the package name currently being edited, or None."""
        name = os.path.basename(self._guess_folder())
        return name if name != "User" else None

    def _guess_folder(self):
        """Return the path to either the package currently being edited, or User."""
        folders = self.window.folders()
        # Test if we have exactly one folder; don't deal with any other number
        if len(folders) == 1:
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
