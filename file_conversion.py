import os
import time

import sublime

from sublime_lib import WindowAndTextCommand
from sublime_lib.path import path_to_dict
from fileconv import *


# build command
class ConvertFileCommand(WindowAndTextCommand):
    """Convert a file (view's buffer) of type ``source`` to type ``target``.

        Supports the following parsers/loaders:
            json
            plist
            yaml

        Supports the following writers/dumpers:
            json
            plist
            yaml

        The file extesion is determined by a special algorythm using
        "appendixes". Here are a few examples:
            ".YAML-ppplist" yaml  -> plist ".ppplist"
            ".json"         json  -> yaml  ".yaml"
            ".json"         yaml  -> plist ".PLIST-json"

        Whether the parser is considered valid is determined from the extesion,
        the extesion + appendix or the view's base scope.

        The different dumpers try to validate the data passed.
        This works well for json -> anything, because json only defines
        strings, numbers, lists and objects (dicts, arrays, hash tables).
    """
    def run(self, source=None, target=None, *args, **kwargs):
        # Check the environment (view, args, ...)
        if self.view.is_scratch():
            return

        if not source in loaders.get:
            self.status("%s for '%s' not supported/implemented." % ("Loader", source))
            return
        if not target in dumpers.get:
            self.status("%s for '%s' not supported/implemented." % ("Dumper", target))
            return

        if self.view.is_dirty():
            self.status("Please safe the file.")
            return

        file_path = self.view.file_name()
        if not file_path or not os.path.exists(file_path):
            self.status("File does not exist.", file_path)
            return

        start_time = time.time()

        # Init the Loader
        loader = loaders.get[source](self.window, self.view)
        output = loader.output

        try:
            data = loader.load(*args, **kwargs)
        except NotImplementedError, e:
            self.status(str(e), file_path)
            return
        if not data:
            return

        # Determine new file name
        new_ext, prepend_target = loader.get_new_file_ext()
        if prepend_target:
            new_ext = ".%s-%s" % (target.upper(), new_ext[1:])
        new_file_path = path_to_dict(file_path).no_ext + (new_ext or '.' + target)

        # Init the Dumper
        dumper = dumpers.get[target](self.window, self.view, new_file_path, output=output)
        if dumper.dump(data, *args, **kwargs):
            self.status("File conversion successful. (%s -> %s)" % (source, target))

        # Finish
        output.write("[Finished in %.3fs]" % (time.time() - start_time))
        output.finish()

    # TODO: define is_visible / is_enabled and check if parameters
    # are passed when specified in a build system

    def status(self, msg, file_path=None):
        sublime.status_message(msg)
        print "[AAAPackageDev] " + msg + (" (%s)" % file_path if file_path is not None else "")
