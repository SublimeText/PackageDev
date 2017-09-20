try:
    from package_control import events
except ImportError:
    pass
else:
    if events.post_upgrade(__package__):
        # clean up sys.modules to ensure all submodules are reloaded
        import sys
        modules_to_clear = set()
        for module_name in sys.modules:
            if module_name.startswith(__package__):
                modules_to_clear.add(module_name)

        print("[{}] Cleaning up {} cached modules after update…"
              .format(__package__, len(modules_to_clear)))
        for module_name in modules_to_clear:
            del sys.modules[module_name]

# Must be named "plugins_"
# because sublime_plugin claims a plugin module's `plugin` attribute for itself.

from .plugins_ import *  # noqa
