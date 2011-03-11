import sublime
import sublime_plugin

import glob
import os
import sys


# Makes sublime_lib package available for all packages.
if not os.path.join(root_at_packages_path("PackageDev/Lib")) in sys.path:
    sys.path.append(os.path.join(root_at_packages_path("PackageDev/Lib")))


DEBUG = 1
THIS_PACKAGE = "PackageDev"
# if DEBUG: THIS_PACKAGE = "XXX" + THIS_PACKAGE

status = sublime.status_message
error = sublime.error_message
join_path = os.path.join
path_exists = os.path.exists
root_at_packages_path = lambda *leafs: join_path(sublime.packages_path(), *leafs)

DEFAULT_DIRS = (
            "Snippets",
            "Support",
            "Docs",
            "Macros"
            )

# name, default template
DEFAULT_FILES = (
            ("LICENSE.txt", None),
            ("README.rst", root_at_packages_path(THIS_PACKAGE, "Support/README.rst")),
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

    
    def on_cancel(self):
        status('on_cancel')
    
    def on_changed(self):
        status('on_changed')

    def run(self):
        self.window.show_input_panel(
                            "New Package Name", '', self.on_done, None, None)


class DeletePackageCommand(sublime_plugin.WindowCommand):
    def run(self):
        pam = PackageManager()
        pam.browse()


class PackageManager(object):
    
    def is_installed(self, name):
        raise NotImplemented
    
    def exists(self, name):
        return path_exists(root_at_packages_path(name))
    
    def browse(self):
        # Let user choose.
        sublime.active_window().run_command("open_dir", 
                                            {"dir": sublime.packages_path()})
    
    def create_new(self, name):
        print "[NewPackage] Creating new package...",
        print root_at_packages_path(name)
        
        if self.dry_run:
            msg = "[NewPackage] ** Nothing done. This was a test. **"
            print msg
            status(msg)
            return

        # Create top folder, default folders, default files.
        map(os.makedirs, [root_at_packages_path(name, d) for d in DEFAULT_DIRS])
        
        for f, template in [(root_at_packages_path(name, fname), template)
                                        for fname, template in DEFAULT_FILES]:
            with open(f, 'w') as fh:
                if template:
                    content = "".join(open(template, 'r').readlines()) % \
                                                        {"package_name": name}
                    fh.write(content)
        
        msg = "[NewPackage] Created new package '%s'." % name
        print msg
        status(msg)
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run