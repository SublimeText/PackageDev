import sys

# clear modules cache if package is reloaded (after update?)
prefix = __package__ + ".plugins"  # don't clear the base package
for module_name in [
    module_name
    for module_name in sys.modules
    if module_name.startswith(prefix)
]:
    del sys.modules[module_name]
del prefix

from .plugins import *  # noqa
