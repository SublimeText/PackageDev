import sublime
import sublime_plugin

SU_FTYPE_EXT_KEYMAP = ".sublime-keymap"

CONTEXT_VALUE = u"string.quoted.double.json meta.structure.dictionary.value.json meta.structure.dictionary.json meta.structure.array.json meta.structure.dictionary.value.json meta.structure.dictionary.json meta.structure.array.json source.json "
CONTEXT_EMPTY_VALUE = u"punctuation.definition.string.end.json string.quoted.double.json meta.structure.dictionary.value.json meta.structure.dictionary.json meta.structure.array.json meta.structure.dictionary.value.json meta.structure.dictionary.json meta.structure.array.json source.json "
CONTEXT_KEY = u"string.quoted.double.json meta.structure.dictionary.json meta.structure.array.json meta.structure.dictionary.value.json meta.structure.dictionary.json meta.structure.array.json source.json "


def first_caret_in_sel(view):
    try:
        return view.sel()[0].begin()
    except IndexError:
        return None


def reverse_scope(scope):
    return ' '.join(reversed(scope.strip().split(' ')))


def scope_matches(view, where, selector):
    return view.match_selector(where, reverse_scope(selector))


def type_of_context_key(view, caret):
    # Go back until we hit a dict key, return key name.
    # We assume the context is well-formed, so there will be a key.
    while view.scope_name(caret) != CONTEXT_KEY:
            caret -= 1

    return view.substr(view.word(caret))


def has_file_extension(view, ext):
    return view.file_name().endswith(ext)


def has_selections(view):
    return len(view.sel()) > 0


class AutocompleteContextsCommand(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if any((
                not has_file_extension(view, SU_FTYPE_EXT_KEYMAP),
                not has_selections(view)
                )):
                return []
        
        print "ALL GOOD"
        # Complete only values in JSON dicts, and only for contexts.
        # Must be a better way of doing this.
        caret = first_caret_in_sel(view)    
        if view.scope_name(caret) in (CONTEXT_VALUE, CONTEXT_EMPTY_VALUE):
            context_field = type_of_context_key(view, caret)
            completions = []
            if context_field == 'key':
                    print "MATCHED KEY"
                    completions = [
                        ("auto_complete_visible", "auto_complete_visible"),
                        ("has_next_field", "has_next_field"),
                        ("has_prev_field", "has_prev_field"),
                        ("num_selections", "num_selections"),
                        ("overlay_visible", "overlay_visible"),
                        ("panel_visible", "panel_visible"),
                        ("following_text", "following_text"),
                        ("preceding_text", "preceding_text"),
                        ("selection_empty", "selection_empty"),
                        ("setting.", "setting."),
                        ("text", "text"),
                        ("selector", "selector"),
                    ]
            elif context_field == 'operator':
                    print "MATCHED OPERATOR"
                    completions = [
                            ("equal", "equal"),
                            ("not_equal", "not_equal"),
                            ("regex_contains", "regex_contains"),
                            ("not_regex_contains", "not_regex_contains"),
                            ("regex_match", "regex_match"),
                            ("not_regex_match", "not_regex_match"),
                    ]
                 # 
            return completions