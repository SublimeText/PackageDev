import sys

# clear modules cache if package is reloaded (after update?)
assert __package__
prefix = __package__ + ".plugins"  # don't clear the base package
for module_name in [
    module_name
    for module_name in sys.modules
    if module_name.startswith(prefix)
]:
    del sys.modules[module_name]
del prefix

assert __package__
from .plugins import *  # noqa
