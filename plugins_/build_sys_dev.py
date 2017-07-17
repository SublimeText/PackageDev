import sublime_plugin

from .lib.sublime_lib.path import root_at_packages

__all__ = ('NewBuildSystem2Command',)

PACKAGE_NAME = __package__.split('.')[0]

BUILD_SYSTEM_SYNTAX = ("Packages/%s/Package/"
                       "Sublime Text Build System/Sublime Text Build System.tmLanguage"
                       % PACKAGE_NAME)


# Adding "2" to avoid name clash with shipped command.
class NewBuildSystem2Command(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir', root_at_packages('User'))
        v.set_syntax_file(BUILD_SYSTEM_SYNTAX)
        v.set_name('untitled.sublime-build')

        template = """{\n\t"cmd": ["${0:make}"]\n}"""
        v.run_command("insert_snippet", {"contents": template})
