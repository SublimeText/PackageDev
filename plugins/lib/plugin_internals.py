"""Accessors for undocumented `sublime_plugin` internals.

The Sublime API type stubs only cover the documented API,
so all accesses to these internals are funneled through this module
to keep the required type checker suppressions in one place.
"""

import sublime_plugin

__all__ = [
    'all_command_classes',
    'command_classes',
    'find_view_event_listener',
]


def find_view_event_listener(view, listener_class):
    """Return the `listener_class` instance attached to `view`, if any."""
    return sublime_plugin.find_view_event_listener(  # ty: ignore[unresolved-attribute]
        view, listener_class
    )


def all_command_classes():
    """Return the lists of registered command classes for every command type."""
    return sublime_plugin.all_command_classes  # ty: ignore[unresolved-attribute]


def command_classes(command_type):
    """Return the registered command classes for "text", "window" or "app" commands."""
    return {
        "text": sublime_plugin.text_command_classes,  # ty: ignore[unresolved-attribute]
        "window": sublime_plugin.window_command_classes,  # ty: ignore[unresolved-attribute]
        "app": sublime_plugin.application_command_classes,  # ty: ignore[unresolved-attribute]
    }[command_type]
