from sublime_plugin import WindowCommand, TextCommand
import sublime

__all__ = ['WindowAndTextCommand']


class WindowAndTextCommand(WindowCommand, TextCommand):
    """A class to derive from when using a Window- and a TextCommand in one
    class (e.g. when you make a build system that should/could also be called
    from the command palette with the view in its focus).

    Defines both self.view and self.window.

    Be careful that self.window may be ``None`` when called as a
    TextCommand because ``view.window()`` is not really safe and will
    fail in quite a few cases. Since the compromise of using
    ``sublime.active_window()`` in that case is not wanted by every
    command I refused from doing so. Thus, the command's on duty to check
    whether the window is valid.

    Since this class derives from both Window- and a TextCommand it is also
    callable with the known methods, like
    ``window.run_command("window_and_text")``.
    I defined a dummy ``run`` method to prevent parameters from raising an
    exception so this command call does exactly nothing.
    Still a better method than having the parent class (the command you
    will define) derive from three classes with the limitation that this
    class must be the first one (the *Command classes do not use super()
    for multi-inheritance support; neither do I but apparently I have
    reasons).
    """
    def __init__(self, param):
        # no super() call! this would get the references confused
        if isinstance(param, sublime.Window):
            self.window = param
            self._window_command = True  # probably called from build system
            self.typ = WindowCommand
        elif isinstance(param, sublime.View):
            self.view   = param
            self._window_command = False
            self.typ = TextCommand
        else:
            raise TypeError("Something really bad happened and you are responsible")

        self._update_members()

    def _update_members(self):
        if self._window_command:
            self.view = self.window.active_view()
        else:
            self.window = self.view.window()

    def run_(self, *args):
        """Wraps the other run_ method implementations from sublime_plugin.
        Required to update the self.view and self.window variables.
        """
        self._update_members()
        # Obviously `super` does not work here
        self.typ.run_(self, *args)
