import glob
import logging
import os

import sublime
import sublime_plugin


__all__ = ('PackagedevCreatePackageCommand',)

l = logging.getLogger(__name__)


def _archived_packages_in_path(path):
    paths = glob.glob(os.path.join(path, "*.sublime-package"))
    return {os.path.splitext(os.path.basename(p))[0]
            for p in paths}


def _get_default_packages():
    default_path = os.path.join(os.path.dirname(sublime.executable_path()), "Packages")
    return _archived_packages_in_path(default_path)


def _get_installed_packages():
    return _archived_packages_in_path(sublime.installed_packages_path())


def _is_override_package(name):
    existing_packages = _get_default_packages() | _get_installed_packages()
    l.debug("existing packages: %r", existing_packages)
    return name in existing_packages


def _create_package(name):
    path = os.path.join(sublime.packages_path(), name)
    try:
        os.mkdir(path)
    except FileExistsError:
        l.error("Path exists already: %r", path)
    except Exception as e:
        l.exception("Unknown error while creating path %r", path)
    else:
        return path
    return None


def _open_folder_in_st(path):
    sublime.run_command('new_window')
    new_window = sublime.active_window()
    new_window.set_project_data({'folders': [{'path': path}]})
    return new_window


class PackagedevCreatePackageCommand(sublime_plugin.WindowCommand):
    def run(self, name=None):
        if not name:
            self.window.show_input_panel(
                caption="Enter your package name",
                initial_text="",
                on_done=self.run,
                on_change=None,
                on_cancel=None,
            )
            return

        if _is_override_package(name):
            result = sublime.ok_cancel_dialog("A package named {!r} already exists."
                                              " Do you want to create an override package?"
                                              .format(name))
            if not result:
                l.debug("Aborted creation of override package for %r", name)
                return

        path = _create_package(name)
        if not path:
            self.window.status_message("Could not create directory for package {!r}".format(name))
            return
        new_window = _open_folder_in_st(path)

        new_window.run_command('show_overlay',
                               {'overlay': 'command_palette', 'text': "PackageDev: New"})
