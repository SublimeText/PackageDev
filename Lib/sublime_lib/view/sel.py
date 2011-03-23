

def has_sels(view):
    """Returns ``True`` if ``view`` has one selection or more.``
    """
    return len(view.sel()) > 0
