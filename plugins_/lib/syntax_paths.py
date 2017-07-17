"""File to store paths to various syntax files within this package."""

_BASE_TMPL = "Packages/{package_name}/Package/{sub_package_name}/{file_name}{ext}"

_package_name = __package__.split(".")[0]


def _build_path(sub_package_name, file_name=None, textmate=False):
    ext = ".sublime-syntax" if not textmate else ".tmLanguage"
    file_name = file_name or sub_package_name

    return _BASE_TMPL.format(package_name=_package_name,
                             sub_package_name=sub_package_name,
                             file_name=file_name,
                             ext=ext)


# paths to our package
PLIST              = _build_path("Property List")
BUILD_SYSTEM       = _build_path("Sublime Text Build System", textmate=True)
COMMANDS           = _build_path("Sublime Text Commands", "Sublime Commands", textmate=True)
COMPLETIONS        = _build_path("Sublime Text Completions", "Sublime Completions", textmate=True)
KEYMAP             = _build_path("Sublime Text Keymap")
MACROS             = _build_path("Sublime Text Macros", textmate=True)
MOUSEMAP           = _build_path("Sublime Text Mousemap", "Sublime Mouse Map", textmate=True)
SETTINGS           = _build_path("Sublime Text Settings")
SNIPPET            = _build_path("Sublime Text Snippet")
SNIPPET_RAW        = _build_path("Sublime Text Snippet", "Sublime Text Snippet (Raw)")
SYNTAX_DEF         = _build_path("Sublime Text Syntax Definition")
TM_PREFERENCES     = _build_path("TextMate Preferences")
TM_SYNTAX_DEF_JSON = _build_path("TextMate Syntax Definition (JSON)", textmate=True)
TM_SYNTAX_DEF_YAML = _build_path("TextMate Syntax Definition (YAML)", textmate=True)

# paths to default packages
XML = "Packages/XML/XML.tmLanguage"
