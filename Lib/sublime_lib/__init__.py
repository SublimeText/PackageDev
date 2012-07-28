import sublime_plugin
from sublime import Window, View


class WindowAndTextCommand(sublime_plugin.WindowCommand, sublime_plugin.TextCommand):
    """A class to derive from when using a Window- and a TextCommand in one class
    (e.g. when you make a build system that should/could also be called from the command
    palette).

        Defines both self.view and self.window.

        Since this class derives from both Window- and a TextCommand it is also callable
        with the known methods, like ``window.run_command("window_and_text")``.
        I defined a dummy ``run`` method to prevent parameters from raising an exception so
        this command call does exactly nothing.
        Still a better method than having the parent class (the command you will define)
        derive from three classes with the limitation that this class must be the first one
        (the *Command classes do not use super() for multi-inheritance support; neither do I
        but apparently I have reasons).
    """
    def __init__(self, param):
        # no super() call! this would get the references confused
        if isinstance(param, Window):
            self.view   = param.active_view()
            self.window = param
            self._window_command = True  # probably called from build system
        elif isinstance(param, View):
            self.view   = param
            self.window = param.window()
            self._window_command = False
        else:
            raise TypeError("Something really bad happend and you are responsible")

    def run(self, *args, **kwargs):
        pass
