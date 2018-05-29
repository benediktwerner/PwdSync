import collections
import functools


class cached:
    def __init__(self, func):
        self.func = func
        self.cache = {}
        functools.update_wrapper(self, func)

    def __call__(self, *args):
        try:
            if args in self.cache:
                return self.cache[args]
            else:
                return self.cache.setdefault(args, self.func(*args))
        # args is not hashable
        except TypeError:
            return self.func(*args)

    def __repr__(self):
        funcname = self.func.__module__ + '.' + self.func.__name__
        return "<cached function {}>".format(funcname)

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

    def clear(self):
        self.cache.clear()
