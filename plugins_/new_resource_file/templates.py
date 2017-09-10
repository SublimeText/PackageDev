TEMPLATES = dict(
    build_system="""\
{
\t"cmd": ["${0:make}"],
}""",
    commands=R"""[
  { "caption": "Preferences: ${1:${package_name:PackageName}}",
    "command": "edit_settings",
    "args": {
      "base_file": "\${packages}/$1/$1.sublime-settings",
      "default": "{\n\t\$0\n}\n"
    }
  },
  { "caption": "Preferences: $1 Key Bindings",
    "command": "edit_settings",
    "args": {
      "base_file": "\${packages}/$1/Default (\${platform}).sublime-keymap",
      "default": "[\n\t\$0\n]\n"
    }
  },
  { "caption": "$1: Open Readme",
    "command": "open_file",
    "args": {
      "target": "\${packages}/$1/README.md"
    }
  },$0
]""",
    commands_short="""\
[
  { "caption": "${1:${package_name:PackageName}}: ${2:My Caption for the Command Palette}",
    "command": "${3:my_command}" },$0
]""",
    completions="""\
{
    "scope": "source.${1:base_scope}",

    "completions": [
        { "trigger": "${2:some_trigger}", "contents": "${3:$2}" },$0
    ]
}""".replace("    ", "\t"),
    settings="""{
\t$0
}""",
    keymap="""[
\t{ "keys": ["${1:ctrl+shift+h}"], "command": "${2:foo_bar}",$0 },
]""",
    menu="""[
\t$0
]""",
    menu_main=R"""[
  { "id": "preferences",
    "children": [
      { "caption": "Package Settings",
        "mnemonic": "P",
        "id": "package-settings",
        "children": [
          { "caption": "${1:${package_name:PackageName}}",
            "children": [
              { "caption": "README",
                "command": "open_file",
                "args": {
                  "target": "\${packages}/$1/README.md"
                }
              },
              { "caption": "-" },
              { "caption": "Settings",
                "command": "edit_settings",
                "args": {
                  "base_file": "\${packages}/$1/$1.sublime-settings",
                  "default": "{\n\t\$0\n}\n"
                }
              },
              { "caption": "Key Bindings",
                "command": "edit_settings",
                "args": {
                  "base_file": "\${packages}/$1/Default (\${platform}).sublime-settings",
                  "default": "[\n\t\$0\n]\n"
                }
              },$0
            ]
          }
        ]
      }
    ]
  }
]
""",
    # no template for a mousemap because I don't want to encourage usage of it
    snippet_raw="",
    # based on the default "New Syntax..." command
    syntax_def=R"""%YAML 1.2
---
# See http://www.sublimetext.com/docs/3/syntax.html
file_extensions:
  - ec
scope: source.example-c

contexts:
  # The prototype context is prepended to all contexts but those setting
  # meta_include_prototype: false.
  prototype:
    - include: comments

  main:
    # The main context is the initial starting point of our syntax.
    # Include other contexts from here (or specify them directly).
    - include: keywords
    - include: numbers
    - include: strings

  keywords:
    # Keywords are if, else for and while.
    # Note that blackslashes don't need to be escaped within single quoted
    # strings in YAML. When using single quoted strings, only single quotes
    # need to be escaped: this is done by using two single quotes next to each
    # other.
    - match: '\b(if|else|for|while)\b'
      scope: keyword.control.example-c

  numbers:
    - match: '\b(-)?[0-9.]+\b'
      scope: constant.numeric.example-c

  strings:
    # Strings begin and end with quotes, and use backslashes as an escape
    # character.
    - match: '"'
      scope: punctuation.definition.string.begin.example-c
      push: inside_string

  inside_string:
    - meta_include_prototype: false
    - meta_scope: string.quoted.double.example-c
    - match: '\\.'
      scope: constant.character.escape.example-c
    - match: '"'
      scope: punctuation.definition.string.end.example-c
      pop: true

  comments:
    # Comments begin with a '//' and finish at the end of the line.
    - match: '//'
      scope: punctuation.definition.comment.example-c
      push:
        # This is an anonymous context push for brevity.
        - meta_scope: comment.line.double-slash.example-c
        - match: \$\n?
          pop: true
""",
    tm_preferences="""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>name</key>
  <string>${1:Comments}</string>
  <key>scope</key>
  <string>source.${2:example_c}</string>
  <key>settings</key>
  <dict>
    <key>shellVariables</key>
    <array>
      <dict>
        <key>name</key>
        <string>TM_COMMENT_START</string>
        <key>value</key>
        <string>// </string>
      </dict>
      <dict>
        <key>name</key>
        <string>TM_COMMENT_START_2</string>
        <key>value</key>
        <string>/*</string>
      </dict>
      <dict>
        <key>name</key>
        <string>TM_COMMENT_END_2</string>
        <key>value</key>
        <string>*/</string>
      </dict>
    </array>
  </dict>
  <key>uuid</key>
  <string>%s</string>
</dict>
</plist>""",  # noqa - line length
    # Technically ST does not use uuids at all,
    # but we leave it in for TextMate compatability
    tm_syntax_def_yaml="""\
# [PackageDev] target_format: plist, ext: tmLanguage
---
name: ${1:Syntax Name}
scopeName: source.${2:base_scope}
fileTypes: [$3]
uuid: %s

patterns:
- $0
...""",
    tm_syntax_def_json="""\
// [PackageDev] target_format: plist, ext: tmLanguage
{ "name": "${1:Syntax Name}",
  "scopeName": "source.${2:base_scope}",
  "fileTypes": ["$3"],
  "uuid": "%s",

  "patterns": [
    $0
  ]
}""",
    tm_syntax_def="""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>name</key>
    <string>${1:Syntax Name}</string>
    <key>scopeName</key>
    <string>source.${2:base_scope}</string>
    <key>fileTypes</key>
    <array>
        <string>$3</string>
    </array>
    <key>uuid</key>
    <string>%s</string>

    <key>patterns</key>
    <array>
        $0
    </array>
</dict>
</plist>""".replace("    ", "\t")  # noqa - line length
)
