# for importing the module
from .output_panel import OutputPanel
from ._view import *
from ._view import __all__

__all__ = __all__[:] + ['OutputPanel']
