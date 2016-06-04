__author__ = {"github.com/": ["yarikoptic", "casperdcl"]}
__all__ = ["LazyImport"]


class LazyImport(object):
    def __init__(self, name=None, mod=None, pkg='tqdm'):
        self.__mod = '.'.join((pkg, mod)) if pkg else mod
        self.__name = name
        self.__obj = None

    @property
    def _obj(self):
        if self.__obj is None:
            # mod = __import__(self.__mod, globals=globals(), locals=locals())
            import importlib
            mod = importlib.import_module(self.__mod)
            self.__obj = getattr(mod, self.__name) if self.__name else mod
        return self.__obj

    @property
    def __doc__(self):
        return self._obj.__doc__

    def __call__(self, *args, **kwargs):
        return self._obj(*args, **kwargs)
