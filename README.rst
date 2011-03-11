PackageDev: Development Tools for Sublime Text Packages
=======================================================

A collection of utilities for ``.sublime-package`` developers.

status: experimental


Overview
********

* Create syntax defs in json, convert to tmlanguage
* Create new package skeleton


Commands
********

Text Commands
-------------

* new_syntax_def (1st step)
* new_syntax_def_from_buffer (alt. 1st step)
* json_to_tmlanguage (2nd step)

Window Commands
---------------

* new_package
* delete_package (opens file browser at ``Packages``)


Completions
***********

* sublime text plugin dev (off by default)
	Will clutter your completions list in any kind of python dev.
	To turn on, change scope selector so ``source.python``.

* smart completions for key bindings


Other Tools
***********

* snippets for key bindings, syntax def development
* sublime_lib