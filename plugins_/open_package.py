import glob
import logging
import os

import sublime
import sublime_plugin

from .create_package import (
    open_folder_in_st, get_default_packages, get_installed_packages,
)

__all__ = ('PackagedevOpenPackageCommand',)

OVERRIDE_SUFFIX = " [*Override*]"

logger = logging.getLogger(__name__)


def _list_normal_packages():

    pkgspath = sublime.packages_path()
    folders = glob.glob(os.path.join(pkgspath, "*/", ""))
    names = (os.path.basename(fold.strip("\\/")) for fold in folders)

    existing_packages = get_default_packages() | get_installed_packages()
    for name in names:
        yield (name, name in existing_packages)


class NameInputHandler(sublime_plugin.ListInputHandler):

    def placeholder(self):
        return "Package"

    def list_items(self):
        packages = list(sorted(_list_normal_packages()))
        logger.debug(packages)
        items = [name + (OVERRIDE_SUFFIX if override else "")
                 for name, override in packages]
        return items


class PackagedevOpenPackageCommand(sublime_plugin.WindowCommand):

    def input(self, args):
        return NameInputHandler()

    def run(self, name):
        if not name:
            return
        name = name.split(OVERRIDE_SUFFIX)[0]
        path = os.path.join(sublime.packages_path(), name)
        # TODO find a .sublime-project file and open that instead?
        open_folder_in_st(path)
