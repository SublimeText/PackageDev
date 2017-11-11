# PackageDev - The Sublime Text Meta Package

PackageDev provides syntax highlighting
and other helpful utility for Sublime Text resource files.

Resource files are ways of configuring the Sublime Text text editor
to various extends,
including but not limited to:
custom syntax definitions,
context menus (and the main menu),
and key bindings.

Thus, this package is ideal for package developers,
but even normal users of Sublime Text
who want to configure it to their liking
should find it very useful.


## Installation

Install the package using [Package Control][].
The package's name is <kbd>PackageDev</kbd>.

PackageDev was made for **Sublime Text 3**.
An older unmaintained version
can still be installed for Sublime Text 2, however.

[Package Control]: https://packagecontrol.io/


## Getting Started

Syntax highlighting for various resource files
is available immediately.

Various commands,
for example creating a new resource,
are made available
through the command palette (<kbd>Primary+Shift+P</kbd>)
with the "PackageDev:" prefix
and in the main menu under *Tools → Packages → Package Development*,

*Note*:
The <kbd>Primary</kbd> key refers to
<kbd>Ctrl</kbd> on Windows and Linux
and <kbd>Command</kbd> (<kbd>⌘</kbd>) on macOS.


## Documentation

Detailed documentation is available [at the repository's wiki][wiki].


[wiki]: https://github.com/SublimeText/PackageDev/wiki


## Features Overview

- Syntax definitions for:

  - Build System files
  - Color Scheme files
  - Commands files
  - Completions files
  - Keymap files
  - Macro files
  - Menu files
  - Mousemap files
  - Project files
  - Settings files
  - Snippet files
  - Syntax definition files (both Sublime Text and TextMate)
  - TextMate Preferences (`.tmPreferences`)

- Static and dynamic completions for all the above,
  where sensible.

  Dynamic completions are provided for
  all files expecting command names,
  syntax definitions,
  color schemes,
  and settings files.

- Snippets for some of the above.

  In files holding multiple "entries",
  snippets are available with the trigger `e` and `ee`
  for a short and a long entry, respectively.

- Commands to create a package
  and various resource files with standard templates.

- Checking for unknown settings keys.

- Hover popups for setting keys with a description and their default value.

- And more!

