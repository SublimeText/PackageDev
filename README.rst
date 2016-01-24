==========
PackageDev
==========

Overview
========

PackageDev is a Sublime Text 2 and 3 package
that helps create and edit
syntax definitions,
snippets,
completions files,
build systems
and other Sublime Text extension files.

The general workflow looks like this:

- run ``new_*`` command
  (``new_raw_snippet``, ``new_completions``, ``new_yaml_syntax_def``...)
- edit file
  (with specific snippets, completions, higlighting, build systems...)
- save file

PackageDev commands are typically accessible
through the *Command Palette* (``Ctrl+Shift+P``)
and prefixed by ``PackageDev:``.


Getting Started
===============

#. After installing `Package Control`_,
   use the *Command Palette* (``Ctrl+Shift+P``)
   to select ``Install Package``
   and then search for ``PackageDev``.
#. Access commands from **Tools | Packages | Package Development**
   or the *Command Palette*.

.. _Package Control: https://packagecontrol.io/installation


Syntax Definition Development
=============================

In PackageDev,
syntax definitions are written in YAML_ (previously JSON).
Sublime Text uses Plist_ XML files
with the ``.tmLanguage`` extension,
so they need to be converted before use
or when you want to modify
an already existing syntax definition.

.. _YAML: http://en.wikipedia.org/wiki/YAML
.. _Plist: http://en.wikipedia.org/wiki/Property_list#Mac_OS_X


Creating a New Syntax Definition
********************************

#. Create new template
   (through **Tools | Packages | Package Development**)
   or the *Command Palette*
#. Select ``Convert to ...`` build system
   from **Tools | Build System**
   or leave as ``Automatic``
#. Press ``Ctrl+B`` or ``F7``


Other included resources for syntax definition development:

* Syntax highlighting,
  including Oniguruma regular expressions
* A command to rearrange unsorted
  (or alphabetically sorted) syntax definitions in YAML.
  See the command's detailed docstring in ``file_conversion.py``
  for parameters and more.
* Static and dynamic completions

  * All basic keys like *name* and *captures*.
  * Numbers will be turned into capture group elements.
    This means that typing ``4<tab>``
    results in ``'4': {name: }``.
  * Scope names are completed as per `TextMate naming conventions`_,
    with the last section being the base scope name.
  * Includes are completed as per defined repository keys.

For a good example definition
(as to why using YAML is way better than the plain Plist),
see the `syntax definition for YAML-tmLanguage files`_
and compare it to the converted ``.tmLanuage`` `equivalent`_.

.. _TextMate naming conventions: https://manual.macromates.com/en/language_grammars#naming_conventions
.. _syntax definition for YAML-tmLanguage files: Syntax%20Definitions/Sublime%20Text%20Syntax%20Def%20(YAML).YAML-tmLanguage
.. _equivalent: Syntax%20Definitions/Sublime%20Text%20Syntax%20Def%20(YAML).tmLanguage


Editing Existing Syntax Definitions
***********************************

You can convert JSON or Plist files to YAML any time
(using the ``Convert to...`` build system or command palette),
but for convenience
PackageDev provides a migration command
that takes care of all that,
*and more*.

**This is highly recommended!**
Running ``Convert to YAML and Rearrange Syntax Definition``
will convert the JSON or Plist syntax definition at hand
into YAML and additioally *prettify* it.
To ensure proper markup of the syntax definition,
explicitly convert indentation to spaces
using the ``Indentation: Convert to Spaces`` command
before converting.

You can also run the command ``Rearrange YAML Syntax Definition``
from the *Command Palette* manually
to sort all lines reasonably,
turn strings into their block representation,
remove redundant mapping symbols
and insert line breaks where they're useful.

The precise steps are thus as follows:

#. Open the ``*.JSON-tmLanguage`` or ``*.tmLanguage`` file
   you want to convert.
#. Open the *Command Palette*
   and run the ``Indentation: Convert to Spaces`` command.
#. Open the *Command Palette*
   and run the ``PackageDev: Convert to YAML and Rearrange Syntax Definition`` command.


"Convert to..." Build System
****************************

The "Convert to..." build system
can interchangably convert JSON, YAML and Plist files.
The source format is automatically detected where possible,
and you will then be prompted for the target file's format.
While this is primarily used for syntax definition,
*it can be used for any file*.

It will also adjust the target file's extension,
following a few rules:

* ``I am json.json`` is parsed into
  ``I am json.plist`` (or ``.yaml``).
* ``I am json.JSON-propertyList`` (or ``.YAML-propertyList``) is parsed into
  ``I am json.propertyList``.


You can override both,
the target format and the extension,
by providing an *options* dict in one of the first three lines of a file.
An *options* dict is indicated
by a line comment starting with ``[PackageDev]``.
Everything to the end of the line commend
(or ``-->`` for Plist)
will then be treated as a YAML dict.

Currently supported options are:

* ``target_format``, options: *plist*, *yaml* and *json*
* ``ext``, without leading ``.``

**Example** (YAML): ``# [PackageDev] target_format: plist, ext: tmLanguage``

*Note*:
The JSON parser can handle
JavaScript-like ``//`` and `` /* */`` comments.
For obvious reasons,
comments are not preserved.


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

PackageDev provides a means to edit snippets using snippets.
These snippets are called *raw snippets*.
You can use snippets and snippet-like syntax in many files,
but if you want to create ``.sublime-snippet`` files,
you need to convert raw snippets first.
This converion is done with a command.

Inside ``Support``
you will find a ``.sublime-keymap`` file.
The key bindings in it are included for reference.
If you want them to work,
you need to copy the contents over
to your personal ``.sublime-keymap`` file under ``Packages/User``.

Creating Snippets
*****************

#. Create new raw snippet with included commands
   (**Tools | Packages | Package Development** or *Command Palette*)
#. Edit snippet
#. If needed,
   convert to ``.sublime-snippet`` with included command

You can use raw snippets directly in some files,
like ``.sublime-completions`` files.


Completions Development
=======================

* Syntax definition for ``.sublime-completions`` files
* Snippets

You can use raw snippets
directly in the ``contents`` element
of a trigger-based completion.


Settings File Development
=========================

* Syntax definition for ``.sublime-settings`` files
* Snippets


About Snippets in PackageDev
============================

The ``Snippets`` folder contains many snippets
for all kinds of development mentioned above.
These snippets follow memorable rules
to make their use easy.

The snippets used more often
have short tab triggers like
``f`` (*field*),
``c`` (*completion*),
``k`` (*key binding*),
etc.
In cases where increasingly complex items
of a similar kind might exist
(numbered fields,
fields with place holders and fields
with substitutions in the case of snippets),
their tab triggers will consist
in a repeated character,
like ``f``, ``ff`` and ``fff``.

As a rule of thumb,
the more complex the snippet,
the longer its tab trigger.

Also,
``i`` (for *item*) is often a generic synonym
for the most common snippet in a type of file.
In such cases,
``ii`` and even longer tab triggers might work too,
for consistency.


Sublime Library
===============

PackageDev previously included ``sublime_lib``,
a Python module with utilities for plugin developers.
It will be made available as a Package Control dependency soon™.
