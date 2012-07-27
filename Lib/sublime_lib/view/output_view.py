from ._view import append, clear


class OutputView(object):
    """This class represents an output view (which are used for e.g. build systems).

    OutputView(window, panel_name, file_regex=None, path=None)
        * window
            The window. This is usually ``self.window`` or ``self.view.window()``,
            depending on the type of your command.

        * panel_name
            The panel's name, passed to ``window.get_output_panel()``.

        * file_regex
            Important for Build Systems. The user can browse the errors you write
            with F4 and Shift+F4 keys. The error's location is determined with 3
            capturing groups: the file name, the line number and the column.

            Example:
                r"Error in file "(.*?)", line (\d+), column (\d+)"

        * path
            This is only needed if you specify the file_regex param and will be used
            as the root dir for relative filenames when determining error locations.

    Useful attributes:

        view
            The view handle of the output view.
            Can be passed to ``in_one_edit(output.view)`` to group modifications.

    Defines the following methods:

        set_path(path, file_regex=None)
            Used to update the path (and optionally the file_regex) when called.
            The file_regex is updated automatically because it might happen that
            the same panel_name is used multiple times. If file_regex is omitted
            or ``None`` it will be reset to the latest regex specified (when
            creating the instance or from the last call of set_regex/path).

        set_regex(file_regex=None)
            Subset of set_path. Read there for further information.

        write(text)
        write(edit, text)
            Will just write into the output view while appending ``text``.
            The edit parameter can be omitted, in this case the first parameter
            will be used as the text to be written.

            * edit
                An instance of sublime.Edit to be passed View.insert().
                Can be omitted, in this case the function will create its own edit.

            * text
                Will be appended to the output view.

        writeln(text)
        writeln(edit, text)
            Same as write() but inserts a newline at the end.

        clear(edit=None)
            Erases all text in the output view. edit can be omitted.

            * edit
                An instance of sublime.Edit to be passed View.insert().
                Can be omitted, in this case the function will create its own edit.

        show()
        hide()
            Show or hide the output view (= panel).
    """
    def __init__(self, window, panel_name, file_regex=None, path=None):
        self.window = window
        self.panel_name = panel_name
        self.view = window.get_output_panel(panel_name)

        self.set_path(path, file_regex)

    def set_path(self, path, file_regex=None):
        """Update the view's result_base_dir pattern.
        """
        if path is not None:
            self.view.settings().set("result_base_dir", path)
        # Also update the file_regex
        self.set_regex(file_regex)

    def set_regex(self, file_regex=None):
        """Update the view's result_file_regex pattern.
        """
        if file_regex is not None:
            self.file_regex = file_regex
        self.view.settings().set("result_file_regex", self.file_regex)
        # Call get_output_panel so that it'll be picked up as a result buffer
        self.window.get_output_panel(self.panel_name)

    def write(self, edit, text=None):
        """Writes ``text`` to the output window. ``edit`` parameter can be omitted.
        Alias for ``sublime_lib.view.append(self.view, edit, text)``.
        """
        append(self.view, edit, text)

    def writeln(self, edit, text=None):
        """Writes ``text`` to the output window and starts a new line. ``edit`` parameter can be omitted.
        """
        if text is None:
            text = edit
            edit = None

        self.write(edit, text + "\n")

    def clear(self, edit=None):
        """Clears the output window. ``edit`` parameter can be omitted.
        """
        clear(self.view, edit)

    def show(self):
        """Makes the output window visible.
        """
        self.window.run_command("show_panel", {"panel": "output.%s" % self.panel_name})

    def hide(self):
        """Makes the output window invisible.
        """
        self.window.run_command("hide_panel", {"panel": "output.%s" % self.panel_name})
