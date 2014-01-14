import sublime
import sublime_plugin

import os

from sublime_lib.path import root_at_packages, get_package_name

PLUGIN_NAME = get_package_name()


DEBUG = 1

status = sublime.status_message
error = sublime.error_message
join_path = os.path.join
path_exists = os.path.exists

DEFAULT_DIRS = (
    "Snippets",
    "Support",
    "Docs",
    "Macros",
    "bin",
    "data"
)

# name, default template
DEFAULT_FILES = [
    ("LICENSE.txt", None),
    ("README.rst",             "data/README.rst"),
    (".hgignore",              "data/hgignore.txt"),
    (".gitignore",             "data/gitignore.txt"),
    ("bin/MakeRelease.ps1",    "data/MakeRelease.ps1"),
    ("bin/CleanUp.ps1",        "data/CleanUp.ps1"),
    ("data/html_template.txt", "data/html_template.txt"),
    ("data/main.css",          "data/main.css"),
    ("setup.py",               "data/setup.py")
]
for i, (name, path) in enumerate(DEFAULT_FILES):
    if path is not None:
        DEFAULT_FILES[i] = (
            os.path.join(*name.split("/")),
            root_at_packages(PLUGIN_NAME, os.path.join(*path.split("/")))
        )


class NewPackageCommand(sublime_plugin.WindowCommand):

    def on_done(self, pkg_name):
        pam = PackageManager()
        if pam.exists(pkg_name):
            error("  NewPackage -- Error\n\n"
                  "  Package '" + pkg_name + "' already exists.\n"
                  "  You cannot overwrite an existing package."
                  )
            return

        pam.create_new(pkg_name)

    def run(self):
        self.window.show_input_panel("New Package Name", '', self.on_done)


class DeletePackageCommand(sublime_plugin.WindowCommand):
    def run(self):
        pam = PackageManager()
        pam.browse()


class PackageManager(object):

    def is_installed(self, name):
        raise NotImplemented

    def exists(self, name):
        return path_exists(root_at_packages(name))

    def browse(self):
        # Let user choose.
        sublime.active_window().run_command(
            "open_dir",
            {"dir": sublime.packages_path()}
        )

    def create_new(self, name):
        print("[NewPackage] Creating new package...")
        print(root_at_packages(name))

        if self.dry_run:
            msg = "[NewPackage] ** Nothing done. This was a test. **"
            print(msg)
            status(msg)
            return

        # Create top folder, default folders, default files.
        map(os.makedirs, [root_at_packages(name, d) for d in DEFAULT_DIRS])

        for fname, template in DEFAULT_FILES:
            with open(root_at_packages(name, fname), 'w') as fh:
                if template:
                    try:
                        content = ("".join(open(template, 'r').readlines())
                                   % {"package_name": name})
                    except:
                        pass
                    finally:
                        content = "".join(open(template, 'r').readlines())

                    fh.write(content)

        msg = "[NewPackage] Created new package '%s'." % name
        print(msg)
        status(msg)

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
