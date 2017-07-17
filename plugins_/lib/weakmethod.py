# https://code.activestate.com/recipes/81253/

from weakref import ref


class _weak_callable:

    def __init__(self, obj, func):
        self._obj = obj
        self._meth = func

    def __call__(self, *args, **kws):
        if self._obj is not None:
            return self._meth(self._obj, *args, **kws)
        else:
            return self._meth(*args, **kws)

    def __getattr__(self, attr):
        if attr == '__self__':
            return self._obj
        elif attr == '__func__':
            return self._meth
        raise AttributeError(attr)


class WeakMethod: # noqa: D
    """ Wraps a function or, more importantly, a bound method, in
    a way that allows a bound method's object to be GC'd, while
    providing the same interface as a normal weak reference. """

    def __init__(self, fn):
        try:
            self._obj = ref(fn.__self__)
            self._meth = fn.__func__
        except AttributeError:
            # It's not a bound method.
            self._obj = None
            self._meth = fn

    def __call__(self):
        if self._obj is None:
            return _weak_callable(None, self._meth)
        else:
            obj = self._obj()
            if obj is None:
                return None
            else:
                return _weak_callable(obj, self._meth)

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self._obj == other._obj
            and self._meth == other._meth
        )


class WeakMethodProxy(WeakMethod):

    def __call__(self, *args, **kwargs):
        func = super().__call__()
        if func is None:
            raise ReferenceError('weak reference is gone')
        else:
            return func(*args, **kwargs)
