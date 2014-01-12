import sublime_plugin

from sublime_lib.path import root_at_packages, get_package_name

PLUGIN_NAME = get_package_name()

BUILD_SYSTEM_SYNTAX = "Packages/%s/Syntax Definitions/Sublime Text Build System.tmLanguage" % PLUGIN_NAME


# Adding "2" to avoid name clash with shipped command.
class NewBuildSystem2Command(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir', root_at_packages('User'))
        v.set_syntax_file(BUILD_SYSTEM_SYNTAX)
        v.set_name('untitled.sublime-build')

        template = """{\n\t"cmd": ["${0:make}"]\n}"""
        v.run_command("insert_snippet", {"contents": template})
