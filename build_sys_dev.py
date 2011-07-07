import sublime, sublime_plugin

from sublime_lib.path import root_at_data


BUILD_SYSTEM_SYNTAX = 'Packages/AAAPackageDev/Support/Sublime Text Build System.tmLanguage'


# '2' differentiates this command from the one shipped with Sublime.
class NewBuildSystem2Command(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir', root_at_data('Packages/User'))
        v.set_syntax_file(BUILD_SYSTEM_SYNTAX)
        v.set_name('untitled.sublime-build')

        template = """{\n\t"cmd": ["${0:make}"]\n}"""
        v.run_command("insert_snippet", {"contents": template})
