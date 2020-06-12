try:
    from package_control import events
except ImportError:
    pass
else:
    if events.post_upgrade(__package__):
        # clean up sys.modules to ensure all submodules are reloaded
        import sys
        prefix = __package__ + "."  # don't clear the base package
        modules_to_clear = {
            module_name
            for module_name in sys.modules
            if module_name.startswith(prefix) and module_name != __name__
        }

        print("[{}] Cleaning up {} cached modules after update…"
              .format(__package__, len(modules_to_clear)))
        for module_name in modules_to_clear:
            del sys.modules[module_name]

from .plugins import *  # noqa
