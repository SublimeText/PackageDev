

def has_file_extension(view, ext):
    if not ext or not ext.replace('.', ''): return False
    if not ext.startswith('.'):
        ext = '.' + ext
    return view.file_name().endswith(ext)