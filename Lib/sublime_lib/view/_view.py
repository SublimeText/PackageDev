

def has_sels(view):
    """Returns ``True`` if ``view`` has one selection or more.``
    """
    return len(view.sel()) > 0


def has_file_ext(view, ext):
    """Returns ``True`` if view has file extension ``ext``.
    ``ext`` may be specified with or without leading ``.``.
    """
    if not view.file_name(): return False
    if not ext.strip().replace('.', ''): return False
    
    if not ext.startswith('.'):
        ext = '.' + ext

    return view.file_name().endswith(ext)