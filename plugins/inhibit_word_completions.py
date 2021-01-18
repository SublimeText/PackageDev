# This plugin serves as a workaround
# to inhibit word completions for scopes
# that we provide an exclusive list of completions for
# via .sublime-completions files.
#
# Upstream feature request: https://github.com/sublimehq/sublime_text/issues/3643

import sublime
import sublime_plugin

__all__ = (
    'InhibitWordCompletionsListener',
)

selectors = [
    # Property List
    "text.xml.plist meta.tag.xml - punctuation.definition.tag.begin.xml",
    "meta.inside-plist.plist - (comment | meta.tag | meta.inside-value | meta.inside-dict-key)",
    # Build System
    "meta.main-key.sublime-build",
    "(meta.build.collection.sublime-build | meta.variant.sublime-build) - meta.cmd - string",
    "meta.placeholder-name.sublime-build | keyword.other.block.end.placeholder.sublime-build",
    # Color Scheme
    "meta.corner-style.sublime-color-scheme",
    "meta.font-style.sublime-color-scheme",
    "meta.underline-style.sublime-color-scheme",
    "meta.globals-key.sublime-color-scheme",
    "meta.main-key.sublime-color-scheme",
    "meta.rule-key.sublime-color-scheme",
    "meta.globals.sublime-color-scheme - string",
    "meta.color-scheme.collection.sublime-color-scheme - meta.mapping meta.mapping - meta.sequence - string",
    "meta.rule.sublime-color-scheme - meta.sequence meta.sequence - string",
    # Commands
    "meta.main-key.sublime-commands",
    "meta.sublime-commands.collection.sublime-commands meta.mapping - string",
    # Completions
    "meta.completions-key.sublime-completions",
    "meta.completions.sublime-completions meta.mapping - string",
    "meta.kind.sublime-completions",
    "meta.main-key.sublime-completions",
    "meta.completions.collection.sublime-completions - meta.completions.sublime-completions - string",
    # Keymap
    "meta.context.key-value.key.unknown.sublime-keymap",
    "meta.unknown-context-key.sublime-keymap",
    "meta.keybinding-context.sublime-keymap - meta.keybinding-context meta.mapping.value - string",
    "meta.context.key-value.match-all.sublime-keymap",
    "meta.context.key-value.operator.unknown.sublime-keymap",
    "meta.key-chord.sublime-keymap",
    "meta.unknown-main-key.sublime-keymap",
    "source.json.sublime.keymap meta.mapping - meta.mapping meta - string",
    # Macro
    "meta.main-key.sublime-macro",
    "meta.macro.collection.sublime-macro meta.mapping - string - meta.mapping meta.mapping",
    # Menu
    "meta.main-key.sublime-menu",
    "meta.menu.collection.sublime-menu meta.mapping - string",
    "meta.platform-name.sublime-menu",
    # Mousemap
    "meta.button-name.sublime-mousemap",
    "meta.main-key.sublime-mousemap",
    "meta.mousebinding.collection.sublime-mousemap meta.mapping - meta.mapping meta.mapping",
    "meta.modifiers.sublime-mousemap string.quoted.double.json",
    # Project
    # "meta.project.build.sublime-project meta.main-key.sublime-build",
    "meta.project.build.sublime-project - meta.project.build.sublime-project meta.mapping meta - string",
    "meta.folder-key.sublime-project",
    "meta.project.folder.sublime-project - meta.project.folder.sublime-project meta.sequence - string",
    "meta.main-key.sublime-project",
    "meta.project.sublime-project - meta.mapping meta.mapping - meta.sequence - string",
    # Theme
    "meta.attributes-sequence.sublime-theme",
    "meta.class-selector.sublime-theme",
    "meta.interpolation-key.sublime-theme",
    "meta.interpolation-mapping.sublime-theme - string",
    "meta.main-key.sublime-theme",
    "meta.theme.sublime-theme - meta.mapping meta.mapping - meta.sequence - string",
    "meta.parent-key.sublime-theme",
    "meta.parent-mapping.sublime-theme - meta.parent-mapping.sublime-theme meta meta - string",
    "meta.platforms-sequence.sublime-theme",
    "meta.rule-key.sublime-theme",
    "meta.rule.sublime-theme - meta.rule.sublime-theme meta meta - string",
    "meta.texture-key.string.sublime-theme",
    "meta.texture-mapping.sublime-theme - meta.texture-mapping.sublime-theme meta.sequence - string",
    # TextMate Preferences
    "meta.main-key-wrapper.tmPreferences - (meta.tag - punctuation.definition.tag.begin.xml)",
    "text.xml.plist.textmate.preferences meta.inside-dict - (meta.inside-dict.settings.tmPreferences | meta.inside-array | meta.inside-dict-key | meta.inside-value | meta.tag | comment) - meta.inside-dict-key",
    "meta.settings-key-wrapper.tmPreferences - (meta.tag - punctuation.definition.tag.begin.xml)",
    "meta.inside-dict.settings.tmPreferences - meta.inside-array - meta.inside-dict-key - meta.inside-value - meta.tag",
    "meta.shellVariable-name.wrapper.tmPreferences - (meta.tag - punctuation.definition.tag.begin.xml)",
]
selector = " | ".join("({})".format(s) for s in selectors) + " - comment"


class InhibitWordCompletionsListener(sublime_plugin.EventListener):

    # TODO run for syntaxes we're interested in?
    def on_query_completions(self, view, prefix, locations):
        import time
        start = time.time()
        have_completions = all(view.match_selector(point, selector) for point in locations)
        print(time.time() - start)
        if have_completions:
            print("inhibiting word completions")
            # TODO the flag is ignored for empty completions lists
            return [], sublime.INHIBIT_WORD_COMPLETIONS
