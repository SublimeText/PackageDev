import logging
import sublime


# The following available add_region styles are taken from the API documentation:
# http://www.sublimetext.com/docs/3/api_reference.html#sublime.View
# unfortunately, the `sublime` module doesn't encapsulate them for easy reference
# so we hardcode them here.
# TODO use `enum` lib
ADD_REGION_STYLE_NAMES = {
    'DRAW_EMPTY', 'HIDE_ON_MINIMAP', 'DRAW_EMPTY_AS_OVERWRITE', 'DRAW_NO_FILL',
    'DRAW_NO_OUTLINE', 'DRAW_SOLID_UNDERLINE', 'DRAW_STIPPLED_UNDERLINE',
    'DRAW_SQUIGGLY_UNDERLINE', 'HIDDEN', 'PERSISTENT',
}

logger = logging.getLogger(__name__)


def style_flags_from_list(style_list):
    style_flags = 0
    if not isinstance(style_list, list):
        raise TypeError("Expected style *list*")
    for style in style_list:
        if style in ADD_REGION_STYLE_NAMES:
            style_flags |= getattr(sublime, style)
        else:
            logger.debug("Style flag %r doesn't exist", style)
    return style_flags
