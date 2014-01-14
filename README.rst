=============
AAAPackageDev
=============

Overview
========

AAAPackageDev is a Sublime Text 2 and 3 plugin that helps create and edit syntax definitions,
snippets, completions files, build systems and other Sublime Text extensions.

The general workflow looks like this:

- run ``new_*`` command (``new_raw_snippet``, ``new_completions``, ``new_yaml_syntax_def``...)
- edit file (with specific snippets, completions, higlighting, build systems...)
- save file

AAAPackageDev ``new_*`` commands are typically accessible through the *Command Palette*
(``Ctrl+Shift+P``).


Getting Started
===============

#. After installing `Package Control`_, use the *Command Palette* (``Ctrl+Shift+P``) to select
   ``Install Package`` and then search for ``AAAPackageDev``.
#. Access commands from **Tools | Packages | Package Development** or the *Command Palette*.

Alternatively, download and install `AAAPackageDev`_ manually. (See `installation instructions`_ for
``.sublime-package`` files.)

.. _Package Control: https://sublime.wbond.net/installation
.. _AAAPackageDev: https://bitbucket.org/guillermooo/aaapackagedev/downloads/AAAPackageDev.sublime-package
.. _installation instructions: http://sublimetext.info/docs/en/extensibility/packages.html#installation-of-packages


Syntax Definition Development
=============================

In AAAPackageDev, syntax definitions are written in YAML_ (previously JSON). Sublime Text uses
Plist_ XML files with the ``.tmLanguage`` extensions, so they need to be converted before use if you
want to modify an already existing. The conversion is done through the included build system
``Convert to...``. You can then run the command ``Rearrange YAML Syntax Definition`` from the
*Command Palette* to sort all lines reasonably and insert line breaks where they're useful.
Alternatively you can run ``Convert to YAML and Rearrange Syntax Definition`` to do everything at
once.

.. _YAML: http://en.wikipedia.org/wiki/YAML
.. _Plist: http://en.wikipedia.org/wiki/Property_list#Mac_OS_X


Creating a New Syntax Definition
********************************

#. Create new template (through **Tools | Packages | Package Development**) or the *Command Palette*
#. Select ``Convert to ...`` build system from **Tools | Build System** or leave as ``Automatic``
#. Press ``F7`` or ``Ctrl+B``


Other included resources for syntax definition development:

* Syntax highlighting, including Oniguruma regular expressions
* A command to rearrange unsorted (or alphabetically sorted) syntax definitions in YAML. See the
  command's detailed docstring in ``file_conversion.py`` for parameters and more.
* Static and dynamic completions

  * All basic keys like *name* and *captures*.
  * Numbers will automatically be turned into capture groups. This means that typing ``4<tab>``
    results in ``'4': {name: }``.
  * Scope names are completed as per `TextMate naming conventions`_, with the last section being
    the base scope name.
  * Includes are completed as per defined repository keys.

To make best usage of the auto completions for scopes, ``{ characters": ".", "selector": "source.yaml-tmlanguage - comment" }`` should be added to the "auto_complete_triggers" setting.

For a good example definition (as to why using YAML is way better than the plain Plist), see the
syntax definition for YAML-tmLanguage files: `Sublime Text Syntax Def (YAML).YAML-tmLanguage`_

.. _TextMate naming conventions: https://manual.macromates.com/en/language_grammars#naming_conventions
.. _Sublime Text Syntax Def (YAML).YAML-tmLanguage: Syntax%20Definitions/Sublime%20Text%20Syntax%20Def%20(YAML).YAML-tmLanguage


"Convert to..." Build System
******************************

The "Convert to..." build system can interchangably convert JSON, YAML and Plist files. The source
format is automatically detected, as long as it's possible, and will then prompt you for the target
file's format. While this is primarily used for syntax definition it can be used for any file.

It will also adjust the target file's extension, following a few rules:

* ``I am json.json`` will be parsed into ``I am json.plist``.
* ``I am json.JSON-propertyList`` will be parsed into ``I am json.propertyList``.


You can override both, the target format and the extension, by providing an options dict in one of the
first three lines of a file. An options dict is indicated by a line comment with following
``[PackageDev]``. Everything to the end of the line commend (or ``-->`` for Plist) will then be
treated as a YAML dict.

Currently supported options are:
* ``target_format``, options: *plist*, *yaml* and *json*
* ``ext``, without leading ``.``

**Example** (YAML): ``# [PackageDev] target_format: plist, ext: tmLanguage``

*Note*: The JSON parser can handle JavaScript-like ``//`` and `` /* */`` comments.


Package Development
===================

Resources for package development are in a very early stage.

Commands
********

``new_package``
	Window command. Prompts for a name and creates a new package skeleton in ``Packages``.

``delete_package``
	Window command. Opens file browser at ``Packages``.


.. Completions
.. -----------
..
.. * sublime text plugin dev (off by default)
.. Will clutter your completions list in any kind of python dev.
.. To turn on, change scope selector to ``source.python``.


Build System Development
========================

* Syntax definition for ``.build-system`` files.


Key Map Development
===================

* Syntax definition for ``.sublime-keymap`` files.
* Completions
* Snippets


Snippet Development
===================

AAAPackageDev provides a means to edit snippets using snippets. These snippets
are called *raw snippets*. You can use snippets and snippet-like syntax in many
files, but if you want to create ``.sublime-snippet`` files, you need to convert
raw snippets first. This converion is done with a command.

Inside ``AAAPackageDev/Support`` you will find a ``.sublime-keymap`` file.
The key bindings in it are included for reference. If you want them to work,
you need to copy the contents over to your personal ``.sublime-keymap`` file
under ``Packages/User``.

Creating Snippets
*****************

#. Create new raw snippet with included commands (**Tools | Packages | Package Development** or
   *Command Palette*)
#. Edit snippet
#. If needed, convert to ``.sublime-snippet`` with included command

You can use raw snippets directly in some files, like ``.sublime-completions`` files.


Completions Development
=======================

* Syntax definition for ``.sublime-completions`` files
* Snippets

You can use raw snippets directly in the ``contents`` element of a trigger-based
completion.


Settings File Development
=========================

* Syntax definition for ``.sublime-settings`` files
* Snippets


About Snippets in AAAPackageDev
===============================

The ``AAAPackageDev/Snippets`` folder contains many snippets for all kinds of
development mentioned above. These snippets follow memorable rules to make their
use easy.

The snippets used more often have short tab triggers like ``f`` (*field*),
``c`` (*completion*), ``k`` (*key binding*), etc. In cases where increasingly
complex items of a similar kind might exist (numbered fields, fields with place
holders and fields with substitutions in the case of snippets), their tab triggers
will consist in a repeated character, like ``f``, ``ff`` and ``fff``.

As a rule of thumb, the more complex the snippet, the longer its tab trigger.

Also, ``i`` (for *item*) is often a generic synonym for the most common snippet
in a type of file. In such cases, ``ii`` and even longer tab triggers might work
too for consistency.


Sublime Library
===============

AAAPackageDev includes ``sublime_lib``, a Python package with utilities for
plugin developers. Once AAAPackageDev is installed, ``sublime_lib`` will be
added to Python's PATH and importable from any other plugin.
