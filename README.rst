=============
AAAPackageDev
=============

status: beta

Overview
********

AAAPackageDev streamlines creation of snippets, completions files, build systems
and nearly any other Sublime Text extension.

The general workflow looks like this:

- execute ``new_*`` command (``new_raw_snippet``, ``new_completions``, ``new_syntax_def``...)
- edit file (with specific snippets, completions, higlighting, build systems...)
- save file

AAAPackageDev ``new_*`` commands are typically accessible through the *Command
Palette* (``Ctrl+Shift+P``).


Getting Started
***************

#. Download and install `AAAPackageDev`_.
#. Access commands from **Tools | Packages | Package Development** or the
	*Command Palette* (``Ctrl+Shift+P``).

.. _AAAPackageDev: https://bitbucket.org/guillermooo/aaapackagedev/downloads/AAAPackageDev.sublime-package

If you're running a full installation of Sublime Text, simply double click on any ``.sublime-package`` file to install it.
If you're running a portable installation, you need to do the installation for any ``.sublime-package`` `by hand`_.

.. _by hand: http://sublimetext.info/docs/extensibility/packages.html#installation-of-packages-with-sublime-package-archives


Syntax Definition Development
*****************************

Commands
--------

``new_syntax_def()``
	Window command. Creates a new ``.JSON-tmLanguage`` file.

``new_syntax_def_from_buffer()``
	Text command. Inserts JSON-based template for syntax definitions into the
	active view buffer.

``make_tmlanguage()``
	Window command. Generates ``.tmLanguage`` from ``.JSON-tmLanguage`` from
	active buffer. Intended for use in build systems.

Build Systems
-------------

* ``Json to tmLanguage``
	Converts the current file (``.JSON-tmLanguage``) into a suitable ``.tmLanguage``
	syntax definition (**Tools | Build System**).

Creating a New Syntax Definition
------------------------------------

#. Create new template with any of the above commands
#. Select ``Json to tmLanguage`` build system from **Tools | Build System**
#. Press ``F7``


Package Development
*******************

Commands
--------

``new_package()``
	Window command. Prompts for a name and creates a new package skeleton in ``Packages``.

``delete_package()``
	Window command. Opens file browser at ``Packages``.


.. Completions
.. -----------
.. 
.. * sublime text plugin dev (off by default)
.. Will clutter your completions list in any kind of python dev.
.. To turn on, change scope selector so ``source.python``.

Build System Development
************************

AAAPackageDev includes a comprehensive syntax definition for ``.build-system``
files.


Key Maps
********

AAAPackageDev includes a comprehensive syntax definition for ``.sublime-keymap``
files, in addition to smart completions and snippets for key map development.


Snippet Development
*******************

``new_raw_snippet()``
	Window command. A especial *view* into a snippet for development only (highlighting, snippets...).
``new_raw_snippet_from_snippet()``
	Text command. Creates a new raw snippet from the ``content`` of an open ``.sublime-snippet``.
``generate_snippet_from_raw_snippet()``
	Text command. Generates a snippet file from a raw snippet. Replaces the raw snippet instead of creating a new view.

Creating a New Snippet
----------------------

#. Create new *raw* snippet with any available command
#. Edit snippet using snippets, syntax highlighting, etc.
#. Generate snippet from raw snippet with existing command
#. Save new snippet

.. note:
	All generated snippets must be saved before they can be used.


About Snippets in AAAPackageDev
*******************************

The ``AAAPackageDev/Snippets`` folder contains many snippets for all kinds of
development mentioned above. These snippets follow memorable rules to make their
use easy. 

The snippets used more often have short tab triggers like ``f`` (*field*),
``c`` (*completion*), ``k`` (*key binding*), etc. In cases where increasingly
complex items might exist (for example: numbered fields, fields with place holders
and substitutions, for snippets), their tab triggers will consist in a repeated
character, like ``f``, ``ff`` and ``fff`` ---in the example just mentioned---,
or ``c`` and ``cc`` in ``.sublime-completions`` files (for simple completions
and trigger-based completions, respectively).

In general, the more complex the snippet, the longer its tab trigger.

Also, ``i`` (for *item*) is often a generic synonym for the most common snippet
in a type of file and will insert the same snippet as them. In such cases,
``ii`` and even longer tab triggers might work too for convenience.


Sublime Library
***************

AAAPackageDev includes ``sublime_lib``, a Python package with utilities for
plugin developers. Once AAAPackageDev is installed, ``sublime_lib`` will be
importable from any plugin residing in ``Packages``.