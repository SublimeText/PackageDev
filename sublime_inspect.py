import sublime
import sublime_plugin

import os


class SublimeInspect(sublime_plugin.WindowCommand):
    def on_done(self, s):
        rep = Report(s)
        rep.show()        

    def run(self):
        self.window.show_input_panel("Search String:", '', self.on_done, None, None)


class Report(object):
    def __init__(self, s):
        self.s = s

    def collect_info(self):
        try:
            atts = dir(eval(self.s, {"sublime": sublime, "sublime_plugin": sublime_plugin}))
        except NameError, e:
            atts = e
        
        self.data = atts

    def show(self):
        self.collect_info()
        v = sublime.active_window().new_file()
        v.insert(v.begin_edit(), 0, '\n'.join(self.data))
        v.set_scratch(True)
        v.set_name("SublimeInspect - Report")


class OpenSublimeSessionCommand(sublime_plugin.WindowCommand):
    def run(self):
        session_file = os.path.join(sublime.packages_path(), "..", "Settings", "Session.sublime_session")
        self.window.open_file(session_file)