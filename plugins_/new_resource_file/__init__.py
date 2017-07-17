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
    def run(self, kind):
        if kind not in TEMPLATES:
            l.error("Unknown resource file kind %r", kind)
            return

        v = self.window.new_file()

        # initialize settings (and syntax)
        v.set_syntax_file(_syntax_path_for_kind(kind))
        user_package_path = os.path.join(sublime.packages_path(), "User")
        v.settings().set('default_dir', user_package_path)
        if kind == "tm_syntax_def":
            v.settings().set('default_extension', ".tmLanguage")

        # insert the template
        template = TEMPLATES[kind]
        if kind.startswith("tm_"):
            # tm_* kinds expect a uuid to be inserted
            template = template % uuid.uuid4()
        v.run_command('insert_snippet', {'contents': template})
