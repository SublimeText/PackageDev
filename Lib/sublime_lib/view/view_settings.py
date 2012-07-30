_settable_attributes = ('_s', '_view', '_none_erases')  # allow only setting of these attributes


class ViewSettings(object):
    """Helper class for accessing settings' values from views.

        ViewSettings(view, none_erases=False)

        Defines the default methods for sublime.Settings:

            get(key, default=None)
            set(key, value)
            erase(key)
            has(key)
            add_on_change(key, on_change)
            clear_on_change(key, on_change)

            http://www.sublimetext.com/docs/2/api_reference.html#sublime.Settings

        If ``none_erases == True`` you can erase a key when setting it to
        ``None``. This only has a meaning when the key you erase is defined in
        a parent Settings collection which would be retrieved in that case.

        The following methods can be used to retrieve a setting's value:

            value = self.get('key', default)
            value = self['key']
            value = self.key_without_spaces

        The following methods can be used to set a setting's value:

            self.set('key', value)
            self['key'] = value
            self.key_without_spaces = value

      ! Important:
        Don't use the attribute method with one of these keys (self.dir()):

            ['__class__', '__delattr__', '__dict__', '__doc__', '__format__',
            '__getattr__', '__getattribute__', '__getitem__', '__hash__',
            '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__',
            '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__',
            '__subclasshook__', '__weakref__', '_s', '_none_erases', _view',
            'add_on_change', 'clear_on_change', 'erase', 'get', 'has', 'set']

        Getting will return the respective function, setting will do nothing.
        Setting of _leading_underline_values from above will result in
        unpredictable behavior. Please don't do this! And re-consider even when
        you know what you're doing.
    """
    _view        = None
    _s           = None
    _none_erases = False

    def __init__(self, view, none_erases=False):
        self._view = view
        if not self._view:
            raise ValueError("Invalid view")
        self._s = view.settings()
        if not self._s:
            raise ValueError("Could not resolve view.settings()")
        self._none_erases = none_erases

    def get(self, key, default=None):
        """Returns the named setting, or default if it's not defined.
        """
        return self._s.get(key, default)

    def set(self, key, value):
        """Sets the named setting. Only primitive types, lists, and
        dictionaries are accepted.
        Erases the key iff ``value is None``."""
        if value is None and self._none_erases:
            self.erase(key)
        else:
            self._s.set(key, value)

    def erase(self, key):
        """Removes the named setting. Does not remove it from any parent Settings.
        """
        self._s.erase(key)

    def has(self, key):
        """Returns true iff the named option exists in this set of Settings or
        one of its parents.
        """
        return self._s.has(key)

    def add_on_change(self, key, on_change):
        """Register a callback to be run whenever the setting with this key in
        this object is changed.
        """
        self._s.add_on_change(key, on_change)

    def clear_on_change(self, key, on_change):
        """Remove all callbacks registered with the given key.
        """
        self._s.clear_on_change(key, on_change)

    def __getattr__(self, key):
        """self.key_without_spaces"""
        return self.get(key)

    def __getitem__(self, key):
        """self[key]"""
        return self.get(key)

    def __setattr__(self, key, value):
        """self.key_without_spaces = value"""
        if key in _settable_attributes:
            object.__setattr__(self, key, value)
        else:
            self.set(key, value)

    def __setitem__(self, key, value):
        """self[key] = value"""
        self.set(key, value)
