PackageDev: Development Tools for Sublime Text Packages
=======================================================

A collection of utilities for Sublime Text package developers.

status: alpha


Overview
********

* Tools for creating syntax definitions
* Tools for creating new packages
* Misc tools


Getting Started
***************

#. Download the `latest version`_ and double-click on ``AAAPackageDev.sublime-package``.
#. Access commands from **Tools | Packages | Package Development**.

.. _latest version: https://bitbucket.org/guillermooo/packagedev/downloads/AAAPackageDev.sublime-package


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

Creating a New Syntax Definition
------------------------------------

#. Create new template with any of the above commands
#. Select *Json to tmLanguage* build system
#. Press *F7*


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


Key Bindings
************

*PackageDev* includes a comprehensive syntax definition for ``.sublime-keymap``
files, in addition to smart completions and snippets for key map development.


Sublime Library
***************

*PackageDev* includes ``sublime_lib``, a Python package with utilities for
plugin developers.