import sublime, sublime_plugin

import sublime_lib

import os
import json


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


def gen_files(fname, package_name=''):
    target = os.path.abspath(os.path.join(
                                   sublime.packages_path(),
                                   package_name))
   
    for base, dirs, files in os.walk(target):
        if base.endswith('.hg'): continue
        for f in files:
            if f == fname:
                yield base, f
            

def in_merge_order(fname):
    for dirname in ('Default', '', 'User'):
        for base, f in gen_files(fname, dirname):
            if dirname == '' and (base.endswith('Default') or
                                  base.endswith('User')):
                continue
            yield os.path.join(base, f)


def get_merged_settings(fname):
    merged_settings = {}
 
    for f in in_merge_order(fname):
        settings_raw = json.load(open(f))
        for k,v in settings_raw.iteritems():
            if k in merged_settings:
                merged_settings[k].append((f, v))
            else:
                merged_settings[k] = [(f, v)]
 
    return merged_settings


class InspectFileOptionsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        settings = get_merged_settings('Python.sublime-settings')
        print "=" * 30
        print "Settings for:", self.view.scope_name(0).rsplit(' ')[1]
        print ''
        for k, v in settings.iteritems():
            print k + ":"
            for location, value in v:
                print "\t%s\t\t\t%s" % (value, location)
            print
        print "=" * 30

def to_json_type(v):
    """"Convert string value to proper JSON type.
    """
    try:
        if v.lower() in ("false", "true"):
            v = (True if v.lower() == "true" else False)
        elif v.isdigit():
            v = int(v)
        elif v.replace(".", "").isdigit():
            v = float(v)
    except AttributeError:
        raise ValueError("Conversion to JSON failed for: %s" % v)

    return v



class ShowViewOptionsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.window().show_input_panel('Inspect:', '', self.on_done, None, None)
            
    def on_done(self, s):
        if s == 'set?':
            self.view.run_command('inspect_file_options')
        if s.startswith('set '):
            self.view.settings().set(s.split(' ')[1], to_json_type(s.split(' ')[2]))
        if s.startswith('set?') and '? ' not in s:
            name, value = s.split('?')
            result = self.view.settings().get(value)
            sublime.status_message(unicode(result))
