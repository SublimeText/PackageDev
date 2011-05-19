AAAPackageDev
=============

A collection of utilities for Sublime Text package developers.

status: beta


Overview
********

* Tools for creating syntax definitions
* Tools for creating new packages
* Tools for creating snippets
* Sublime Library


Getting Started
***************

#. Download and install `AAAPackageDev`_.
#. Access commands from **Tools | Packages | Package Development**.

.. _AAAPackageDev: https://bitbucket.org/guillermooo/aaapackagedev/downloads/AAAPackageDev.sublime-package

If you're running a full installation of Sublime Text, simply doubleclick on the ``.sublime-package`` files.
If you're running a portable installation, you need to do the installation `by hand`_ for ``.sublime-package``.

.. _by hand: http://sublimetext.info/docs/extensibility/packages.html#installation-of-packages-with-sublime-package-archives


Syntax Definitions
******************

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

Creating a New Syntax Definition
------------------------------------

#. Create new template with any of the above commands
#. Select ``Json to tmLanguage`` build system
#. Press ``F7``


Packages
********

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

	
Packages
********

``new_package``
	Window command. Prompts for a name and creates a skeleton for a new package.

``delete_package``
	Window command. Opens the file browser at ``Packages``.


Snippets
********

The ``AAAPackageDev/Snippets`` folder contains many snippets for all kinds of
development mentioned above.


Sublime Library
***************

AAAPackageDev includes ``sublime_lib``, a Python package with utilities for
plugin developers.