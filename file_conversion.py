import os
import time

import sublime

from sublime_lib import WindowAndTextCommand
from sublime_lib.path import file_path_tuple
from sublime_lib.view import OutputPanel

try:  # ST3
    from .fileconv import dumpers, loaders
except ValueError:  # ST2
    from fileconv import dumpers, loaders


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

        The different dumpers try to validate the data passed.
        This works best for json -> anything because json only defines
        strings, numbers, lists and objects (dicts, arrays, hash tables).
    """
    # {name:, kwargs:}
    # name is for the quick panel; others are arguments used when running the command again
    target_list = [dict(name=fmt.name,
                        kwargs={"target_format": fmt.ext})
                   for fmt in dumpers.get.values()]
    for i, itm in enumerate(target_list):
        if itm['name'] == "YAML":
            # Hardcode YAML block style, who knows if anyone can use this
            target_list.insert(
                i + 1,
                dict(name="YAML (Block Style)",
                     kwargs={"target_format": "yaml", "default_flow_style": False})
            )

    def run(self, edit=None, source_format=None, target_format=None, ext=None,
            open_new_file=False, rearrange_yaml_syntax_def=False, _output=None, *args, **kwargs):
        """Available parameters:

            edit (sublime.Edit) = None
                The edit parameter from TextCommand. Unused.

            source_format (str) = None
                The source format. Any of "yaml", "plist" or "json".
                If `None`, attempt to automatically detect the format by extension, used syntax
                highlight or (with plist) the actual contents.

            target_format (str) = None
                The target format. Any of "yaml", "plist" or "json".
                If `None`, attempt to find an option set in the file to parse.
                If unable to find an option, ask the user directly with all available format options.

            ext (str) = None
                The extension of the file to convert to, without leading dot. If `None`, the extension
                will be automatically determined by a special algorythm using "appendixes".

                Here are a few examples:
                    ".YAML-ppplist" yaml  -> plist ".ppplist"
                    ".json"         json  -> yaml  ".yaml"
                    ".tmplist"      plist -> json  ".JSON-tmplist"
                    ".yaml"         json  -> plist ".JSON-yaml" (yes, doesn't make much sense)

            open_new_file (bool) = False
                Open the (newly) created file in a new buffer.

            rearrange_yaml_syntax_def (bool) = False
                Interesting for language definitions, will automatically run
                "rearrange_yaml_syntax_def" command on it, if the target format is "yaml".
                Overrides "open_new_file" parameter.

            _output (OutputPanel) = None
                For internal use only.

            *args
                Forwarded to pretty much every relevant call but does not have any effect.
                You can't pass *args in commands anyway.

            **kwargs
                Will be forwarded to both the loading function and the dumping function, after stripping
                unsopported entries. Only do this if you know what you're doing.

                Functions in question:
                    yaml.dump
                    json.dump
                    plist.writePlist (does not support any parameters)

                A more detailed description of each supported parameter for the respective dumper can be
                found in `fileconv/dumpers.py`.
        """
        # TODO: Ditch *args, can't be passed in commands anyway

        # Check the environment (view, args, ...)
        if self.view.is_scratch():
            return

        if self.view.is_dirty():
            # While it works without saving you should always save your files
            return self.status("Please save the file.")

        file_path = self.view.file_name()
        if not file_path or not os.path.exists(file_path):
            # REVIEW: It is not really necessary for the file to exist, technically
            return self.status("File does not exist.", file_path)

        if source_format and target_format == source_format:
            return self.status("Target and source file format are identical. (%s)" % target_format)

        if source_format and not source_format in loaders.get:
            return self.status("%s for '%s' not supported/implemented." % ("Loader", source_format))

        if target_format and not target_format in dumpers.get:
            return self.status("%s for '%s' not supported/implemented." % ("Dumper", target_format))

        # Now the actual "building" starts (collecting remaining parameters)
        output = _output or OutputPanel(self.window, "package_dev")
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
                return output.write_line("\nUnable to detect file type.")
            elif target_format == source_format:
                return output.write_line("File already is %s." % loaders.get[source_format].name)

        # Load inline options
        Loader = loaders.get[source_format]
        opts = Loader.load_options(self.view)

        # Function to determine the new file extension depending on the target format
        def get_new_ext(target_format):
            if ext:
                return '.' + ext
            if opts and 'ext' in opts:
                return '.' + opts['ext']
            else:
                new_ext, prepend_target_format = Loader.get_new_file_ext(self.view)
                if prepend_target_format:
                    new_ext = ".%s-%s" % (target_format.upper(), new_ext[1:])

            return (new_ext or '.' + target_format)

        path_tuple = file_path_tuple(file_path)  # This is the latest point possible

        if not target_format:
            output.write("No target format specified, searching in file...")

            # No information about a target format; ask for it
            if not opts or not 'target_format' in opts:
                output.write(" Could not detect target format.\n"
                             "Please select or define a target format...")

                # Show overlay with all dumping options except for the current type
                # Save stripped-down `items` for later
                options, items = [], []
                for itm in self.target_list:
                    # To not clash with function-local "target_format"
                    target_format_ = itm['kwargs']['target_format']
                    if target_format_ != source_format:
                        options.append(["Convert to: %s" % itm['name'],
                                        path_tuple.base_name + get_new_ext(target_format_)])
                        items.append(itm)

                def on_select(index):
                    target = items[index]
                    output.write_line(' %s\n' % target['name'])

                    kwargs.update(target['kwargs'])
                    kwargs.update(dict(source_format=source_format, _output=output))
                    self.run(*args, **kwargs)

                # Forward all params to the new command call
                self.window.show_quick_panel(options, on_select)
                return

            target_format = opts['target_format']
            # Validate the shit again, but this time print to output panel
            if source_format is not None and target_format == source_format:
                return output.write_line("\nTarget and source file format are identical. (%s)" % target_format)

            if not target_format in dumpers.get:
                return output.write_line("\n%s for '%s' not supported/implemented." % ("Dumper", target_format))

            output.write_line(' %s\n' % dumpers.get[target_format].name)

        start_time = time.time()

        # Okay, THIS is where the building really starts
        # Note: loader or dumper errors are not caught in order to receive a nice traceback in the console
        loader = Loader(self.window, self.view, output=output)

        data = None
        try:
            data = loader.load(*args, **kwargs)
        except NotImplementedError as e:
            # use NotImplementedError to make the handler report the message as it pleases
            output.write_line(str(e))
            self.status(str(e), file_path)

        if data:
            # Determine new file name
            new_file_path = path_tuple.no_ext + get_new_ext(target_format)

            # Init the Dumper
            dumper = dumpers.get[target_format](self.window, self.view, new_file_path, output=output)
            if dumper.dump(data, *args, **kwargs):
                self.status("File conversion successful. (%s -> %s)" % (source_format, target_format))

        # Finish
        output.write("[Finished in %.3fs]" % (time.time() - start_time))
        output.finish()

        if open_new_file or rearrange_yaml_syntax_def:
            new_view = self.window.open_file(new_file_path)

            if rearrange_yaml_syntax_def:
                # For some reason, ST would still indicate the new buffer having "usaved changes"
                # even though there aren't any (calling "save" command here).
                new_view.run_command("rearrange_yaml_syntax_def", {"save": True})

    def status(self, msg, file_path=None):
        sublime.status_message(msg)
        print("[PackageDev] " + msg + (" (%s)" % file_path if file_path is not None else ""))
