PackageDev: Development Tools for Sublime Text Packages
=======================================================

A collection of utilities for Sublime Text package developers.

status: alfa


Overview
********

* Tools for creating syntax definitions
* Tools for creating new packages
* Misc tools


Getting Started
***************

Download the `latest version`_ and double-click on `AAAPackageDev.sublime-package`.

.. _latest version: https://bitbucket.org/guillermooo/packagedev/downloads/AAAPackageDev.sublime-package


Syntax Definitions
******************

Commands
--------

* new_syntax_def (W): Creates a new ``.JSON-tmLanguage`` file.
* new_syntax_def_from_buffer (T): Inserts JSON-based template for syntax definitions
  in an existing buffer.
* make_tmlanguage (W): Generates ``.tmLanguage`` from ``.JSON-tmLanguage`` from currently active buffer.
  Intended for use as a build system.
* apply_package_dev_syntax_def (E): Applies custom syntax definitions to override default associations.

How to Crete a New Syntax Definition
------------------------------------

#. Create new template with any of the above commands
#. Select *Json to tmLanguage* build system
#. Press *F7*


Packages
********

Commands
--------

* new_package: Prompts for a name and creates a new package skeleton.
* delete_package: Opens file browser at ``Packages``.


Completions
-----------

* sublime text plugin dev (off by default)
	Will clutter your completions list in any kind of python dev.
	To turn on, change scope selector so ``source.python``.


Key Bindings
************

* comprehensive syntax def for ``.sublime-keymap`` files
* smart completions for key bindings
* snippets for key binding creation


Sublime Library
***************

* sublime_lib: A Python package with utilities for plugin developers.