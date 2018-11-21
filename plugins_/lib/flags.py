import logging

from sublime_lib.flags import RegionOption

logger = logging.getLogger(__name__)


def style_flags_from_list(style_list):
    style_flags = 0
    if not isinstance(style_list, list):
        raise TypeError("Expected style *list*")
    for style in style_list:
        try:
            style_flags |= RegionOption[style]
        except KeyError:
            logger.debug("Style flag %r doesn't exist", style)
    return style_flags
