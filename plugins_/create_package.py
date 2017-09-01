import logging
import os

import sublime
import sublime_plugin


__all__ = ('PackagedevCreatePackageCommand',)

l = logging.getLogger(__name__)


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

        path = _create_package(name)
        if not path:
            self.window.status_message("Could not create directory for package {!r}".format(name))
            return
        new_window = _open_folder_in_st(path)

        new_window.run_command('show_overlay',
                               {'overlay': 'command_palette', 'text': "PackageDev: New"})
