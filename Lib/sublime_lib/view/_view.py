

def has_file_extension(view, ext):
    if not ext.startswith('.'):
        ext = '.' + ext
    return view.file_name().endswith(ext)