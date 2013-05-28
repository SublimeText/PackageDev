import os
import time

import sublime

from sublime_lib import WindowAndTextCommand
from sublime_lib.path import file_path_tuple
from sublime_lib.view import OutputPanel

from fileconv import *


# build command
class ConvertFileCommand(WindowAndTextCommand):
    """Convert a file (view's buffer) of type ``source_format`` to type
    ``target_format``.

        Supports the following parsers/loaders:
            'json'
            'plist'
            'yaml'

        Supports the following writers/dumpers:
            'json'
            'plist'
            'yaml'

        The file extesion is determined by a special algorythm using
        "appendixes". Here are a few examples:
            ".YAML-ppplist" yaml  -> plist ".ppplist"
            ".json"         json  -> yaml  ".yaml"
            ".tmplist"      plist -> json  ".JSON-tmplist"
            ".yaml"         json  -> plist ".JSON-yaml" (yes, doesn't make much sense)

        Whether the parser is considered valid is determined from the
        extension, the extension + appendix or the view's base scope (or in a
        special case with plist using the file's xml header).
        This is also used to auto-detect the file type if the source parameter
        is omitted.

        The different dumpers try to validate the data passed.
        This works well for json -> anything because json only defines
        strings, numbers, lists and objects (dicts, arrays, hash tables).
    """
    def run(self, source_format=None, target_format=None, *args, **kwargs):
        # If called as a text command...
        self.window = self.window or sublime.active_window()

        # Check the environment (view, args, ...)
        if self.view.is_scratch():
            return

        if self.view.is_dirty():
            # While it works without saving you should always save your files
            return self.status("Please safe the file.")

        file_path = self.view.file_name()
        if not file_path or not os.path.exists(file_path):
            # REVIEW: It is not really necessary for the file to exist
            return self.status("File does not exist.", file_path)

        if source_format and target_format == source_format:
            return self.status("Target and source file format are identical. (%s)" % target_format)

        if source_format and not source_format in loaders.get:
            return self.status("%s for '%s' not supported/implemented." % ("Loader", source_format))

        if target_format and not target_format in dumpers.get:
            return self.status("%s for '%s' not supported/implemented." % ("Dumper", target_format))

        # Now the actual "building" starts
        output = OutputPanel(self.window, "aaa_package_dev")
        output.show()

        # Auto-detect the file type if it's not specified
        if not source_format:
            output.write("Input type not specified, auto-detecting...")
            for Loader in loaders.get.values():
                if Loader.file_is_valid(self.view):
                    source_format = Loader.ext
                    output.write_line(' %s\n' % Loader.name)
                    break

            if not source_format:
                output.write_line("\nCould not detect file type.")
                return
            elif target_format == source_format:
                output.write_line("File already is %s." % loaders.get[source_format].name)
                return

        # Load inline options
        opts = loaders.get[source_format].load_options(self.view)

        if not target_format:
            output.write("No target format specified, searching in file...")

            if not opts or not 'target_format' in opts:
                output.write_line("\nCould not detect target format.")
                output.write_line("Please select or define a target format.")
                # Show overlay and possibly recall the whole command because it's the most simple way
                self.window.run_command('show_overlay', dict(overlay="command_palette", text="Build: "))
                return

            target_format = opts["target_format"]
            # Validate the shit again, this time print to output panel
            if source_format is not None and target_format == source_format:
                return output.write_line("\nTarget and source file format are identical. (%s)" % target_format)

            if not target_format in dumpers.get:
                return output.write_line("\n%s for '%s' not supported/implemented." % ("Dumper", target_format))

            output.write_line(' %s\n' % dumpers.get[target_format].name)

        start_time = time.time()

        # Init the Loader
        loader = loaders.get[source_format](self.window, self.view, output=output)

        data = None
        try:
            data = loader.load(*args, **kwargs)
        except NotImplementedError, e:
            # use NotImplementedError to make the handler report the message as it pleases
            outout.write_line(str(e))
            self.status(str(e), file_path)

        if data:
            # Determine new file name
            if opts and 'ext' in opts:
                new_ext = '.' + opts["ext"]
            else:
                new_ext, prepend_target_format = loader.new_file_ext()
                if prepend_target_format:
                    new_ext = ".%s-%s" % (target_format.upper(), new_ext[1:])

            new_file_path = file_path_tuple(file_path).no_ext + (new_ext or '.' + target_format)

            # Init the Dumper
            dumper = dumpers.get[target_format](self.window, self.view, new_file_path, output=output)
            if dumper.dump(data, *args, **kwargs):
                self.status("File conversion successful. (%s -> %s)" % (source_format, target_format))

        # Finish
        output.write("[Finished in %.3fs]" % (time.time() - start_time))
        output.finish()

    def status(self, msg, file_path=None):
        sublime.status_message(msg)
        print "[PackageDev] " + msg + (" (%s)" % file_path if file_path is not None else "")
