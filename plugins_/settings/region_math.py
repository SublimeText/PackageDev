
# match top-level keys only
KEY_SCOPE = "entity.name.other.key.sublime-settings"
VALUE_SCOPE = (
    "meta.expect-value | meta.mapping.value | "
    "punctuation.separator.mapping.pair.json"
)


def get_key_region_at(view, point):
    """Return the key region if point is on a settings key or None."""
    if view.match_selector(point, KEY_SCOPE):
        for region in view.find_by_selector(KEY_SCOPE):
            if region.contains(point):
                return region
    return None


def get_key_name(view, point):
    """Return the key name if point is on a settings key or None."""
    region = get_key_region_at(view, point)
    return view.substr(region) if region else None


def get_last_key_region(view, point):
    """Return the last key region preceding the specified point or None."""
    last_region = None
    regions = view.find_by_selector(KEY_SCOPE)
    if not regions:
        return None
    for region in regions:
        if region.begin() > point:
            break
        last_region = region
    return last_region


def get_last_key_name_from(view, point):
    """Return the last key name preceding the specified point or None."""
    last_region = get_last_key_region(view, point)
    if last_region:
        return view.substr(last_region)
    else:
        return None


def get_value_region_at(view, point):
    """Return the value region if point is on a settings value or None."""
    if view.match_selector(point, VALUE_SCOPE):
        for region in view.find_by_selector(VALUE_SCOPE):
            if region.contains(point):
                return region
    return None
