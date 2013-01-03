import uuid
import re
import os
import time
import yaml

from sublime import Region, packages_path, INHIBIT_WORD_COMPLETIONS
import sublime_plugin

from sublime_lib.path import root_at_packages
from sublime_lib.view import OutputPanel, in_one_edit, base_scope, get_text, get_viewport_coords, set_viewport

from ordereddict import OrderedDict
from ordereddict_yaml import *

from fileconv import *

PLUGIN_NAME = os.getcwdu().replace(packages_path(), '')[1:]  # os.path.abspath(os.path.dirname(__file__))

BASE_SYNTAX_LANGUAGE = "Packages/%s/Support/Syntax Definitions/Sublime Text Syntax Def (%%s).tmLanguage" % PLUGIN_NAME


# XXX: Move this to a txt file. Let user define his own under User too.
boilerplates = dict(
    json="""{ "name": "${1:Syntax Name}",
  "scopeName": "source.${2:syntax_name}",
  "fileTypes": ["$3"],
  "patterns": [$0
  ],
  "uuid": "%s"
}""",
    yaml="""---
name: ${1:Syntax Name}
scopeName: source.${2:syntax_name}
fileTypes: [$3]
uuid: %s

patterns:
- $0
..."""
)


class NewSyntaxDefCommand(object):
    """Creates a new syntax definition file for Sublime Text with some
    boilerplate text.
    """
    typ = ""

    def run(self):
        target = self.window.new_file()
        target.run_command('new_%s_syntax_def_to_buffer' % self.typ)


class NewJsonSyntaxDefCommand(NewSyntaxDefCommand, sublime_plugin.WindowCommand):
    typ = "json"


class NewYamlSyntaxDefCommand(NewSyntaxDefCommand, sublime_plugin.WindowCommand):
    typ = "yaml"


class NewSyntaxDefToBufferCommand(object):
    """Inserts boilerplate text for syntax defs into current view.
    """
    typ = ""

    def is_enabled(self):
        # Don't mess up a non-empty buffer.
        return self.view.size() == 0

    def run(self, edit):
        self.view.settings().set('default_dir', root_at_packages('User'))
        self.view.settings().set('syntax', BASE_SYNTAX_LANGUAGE % self.typ.upper())

        with in_one_edit(self.view):
            self.view.run_command('insert_snippet', {'contents': boilerplates[self.typ] % uuid.uuid4()})


class NewJsonSyntaxDefToBufferCommand(NewSyntaxDefToBufferCommand, sublime_plugin.TextCommand):
    typ = "json"


class NewYamlSyntaxDefToBufferCommand(NewSyntaxDefToBufferCommand, sublime_plugin.TextCommand):
    typ = "yaml"


###############################################################################


class YAMLTextLoader(loaders.YAMLLoader):
    def _join_multiline(self, string):
        return " ".join([line.strip() for line in string.split("\n")])

    def load(self, text=None, *args, **kwargs):
        if not self.is_valid():
            raise NotImplementedError("Not a %s file." % self.name)
        if text is None:
            text = get_text(self.view)

        self.output.write_line("Parsing %s..." % self.name)
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError, e:
            self.output.write_line(self.debug_base % self._join_multiline(str(e)))
        else:
            return data


class YAMLOrderedTextDumper(dumpers.YAMLDumper):
    default_params = dict(Dumper=OrderedDictSafeDumper)

    def __init__(self, window=None, output=None):
        if isinstance(output, OutputPanel):
            self.output = output
        elif window:
            self.output = OutputPanel(window, self.output_panel_name)

    def sort_keys(self, data, sort_order, sort_numeric):
        def do_sort(obj):
            od = OrderedDict()
            # The usual order
            if sort_order:
                for key in sort_order:
                    if key in obj:
                        od[key] = obj[key]
                        del obj[key]
            # The number order
            if sort_numeric:
                nums = []
                for key in obj:
                    if key.isdigit():
                        nums.append(int(key))
                nums.sort()
                for num in nums:
                    key = str(num)
                    od[key] = obj[key]
                    del obj[key]
            # The remaining stuff
            keys = obj.keys()
            keys.sort()
            for key in keys:
                od[key] = obj[key]
                del obj[key]

            assert len(obj) == 0
            return od

        return self._validate_data(data, (
            (lambda x: isinstance(x, dict), do_sort),
        ))

    def dump(self, data, sort=True, sort_order=False, sort_numeric=True, *args, **kwargs):
        self.output.write_line("Sorting %s..." % self.name)
        self.output.show()
        if sort:
            data = self.sort_keys(data, sort_order, sort_numeric)
        params = self.validate_params(kwargs)
        self.output.write_line("Dumping %s..." % self.name)
        try:
            return yaml.dump(data, **params)
        except Exception, e:
            self.output.write_line("Error dumping %s: %s" % (self.name, e))


class RearrangeYamlSyntaxDefCommand(sublime_plugin.TextCommand):
    """Parses YAML and sorts all the dict keys reasonably.
    Does not write to the file, only to the buffer.

        Parameters:

            sort (bool) = True
                Whether the list should be sorted at all. If this is not
                ``True`` the dicts' keys' order is likely not going to equal
                the input.

            sort_numeric (bool) = True
                A language definition's captures are assigned to a numeric key
                which is in fact a string. If you want to bypass the string
                sorting and instead sort by the strings number value, you will
                want this to be ``True``.

            sort_order (list)
                When this is passed it will be used instead of the default.
                The first element in the list will be the first key to be
                written for ALL dictionaries.
                Set to ``False`` to skip this step.

                The default order is:
                comment, name, scopeName, fileTypes, uuid, begin,
                beginCaptures, end, endCaptures, match, captures, include,
                patterns, repository

            remove_single_maps (bool) = True
                This will in fact turn the "  - {include: '#something'}" lines
                into "  - include: '#something'", which is also valid YAML.
                Be careful inside multi-line strings because this is just a
                simple regexp that's safe for usual syntax definitions.

        Other parameters will be forwarded to yaml.dump (if they are valid).
    """
    sort_order = """comment
        name scopeName fileTypes uuid
        begin beginCaptures end endCaptures match captures include
        patterns repository""".split()

    def is_visible(self):
        return base_scope(self.view) in ('source.yaml', 'source.yaml-tmlanguage')

    def run(self, edit, sort=True, sort_numeric=True, sort_order=None, remove_single_maps=True, **kwargs):
        # Check the environment (view, args, ...)
        if self.view.is_scratch():
            return

        # Collect parameters
        file_path = self.view.file_name()
        if sort_order is None:
            sort_order = self.sort_order
        vp = get_viewport_coords(self.view)

        output = OutputPanel(self.view.window() or sublime.active_window(), "aaa_package_dev")
        output.show()

        self.start_time = time.time()

        # Init the Loader
        loader = YAMLTextLoader(None, self.view, file_path=file_path, output=output)

        data = None
        try:
            data = loader.load()
        except NotImplementedError, e:
            # use NotImplementedError to make the handler report the message as it pleases
            output.write_line(str(e))
            self.status(str(e), file_path)

        if not data:
            return self.finish(output)

        # Dump
        dumper = YAMLOrderedTextDumper(output=output)
        text = dumper.dump(data, sort, sort_order, sort_numeric, **kwargs)
        if not text:
            self.status("Error re-dumping the data.")

        if remove_single_maps:
            # Remove the {} for single list mappings (as a list entry)
            # this does not support all YAML syntaxes but is useful for lang defs
            text = re.sub(r"(?m)^(\s*- )\{([\w-]+: [^,\}]*)\}$", r"\1\2", text)

        # Finish
        self.view.replace(edit, Region(0, self.view.size()), text)
        set_viewport(self.view, vp)
        self.finish(output)

    def finish(self, output):
        output.write("[Finished in %.3fs]" % (time.time() - self.start_time))
        output.finish()

    def status(self, msg, file_path=None):
        sublime.status_message(msg)
        print "[AAAPackageDev] " + msg + (" (%s)" % file_path if file_path is not None else "")


class SyntaxDefCompletions(sublime_plugin.EventListener):
    def __init__(self):
        base_keys = "match,end,begin,name,comment,scopeName,include".split(',')
        dict_keys = "repository,captures,beginCaptures,endCaptures".split(',')
        list_keys = "fileTypes,patterns".split(',')

        completions = list()
        completions.extend(("{0}\t{0}:".format(s), "%s: "    % s) for s in base_keys)
        completions.extend(("{0}\t{0}:".format(s), "%s:\n  " % s) for s in dict_keys)
        completions.extend(("{0}\t{0}:".format(s), "%s:\n- " % s) for s in list_keys)
        completions.extend([
            ("include\tinclude: '#...'", "include: '#$0'"),
            ('include\tinclude: $self',  "include: $self")
        ])

        self.base_completions = completions

    def on_query_completions(self, view, prefix, locations):
        # locations usually has only one entry
        loc = locations[0]

        if not view.match_selector(loc, "source.yaml-tmlanguage"):
            return []

        def inhibit(ret):
            return (ret, INHIBIT_WORD_COMPLETIONS)

        # Extend numerics into `'123': {name: $0}`, as used in captures,
        # but only if they are not in a string scope
        word = view.substr(view.word(loc))
        if word.isdigit() and not view.match_selector(loc, "string"):
            return inhibit([(word, "'%s': {name: $0}" % word)])

        # TODO: naming conventions for scope name
        # if (view.match_selector(loc, "meta.name string") or
        #         view.match_selector(loc - 2, "meta.name keyword.control.definition")):

        # TODO: existing repository keys for includes
        # if (view.match_selector(loc, "variable.other.include"):

        # Do not bother if the syntax def alread matched the current position
        if view.match_selector(loc, "meta"):
            return []

        # Otherwise, use the default completions + generated uuid
        completions = [
            ('uuid\tuuid: ...', "uuid: %s" % uuid.uuid4()),
        ]
        #special: uuid, include, <numbers>

        return inhibit(self.base_completions + completions)
