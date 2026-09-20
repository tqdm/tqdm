"""
Fix v4.0.0..v4.20.0 `__del__` on Python>=3.14.

Should be copied & added to PYTHONPATH
"""
import importlib.util
import inspect
import sys


def _free_pos(cls, instance=None):
    """v4.21.0's message-free implementation"""
    positions = {abs(inst.pos) for inst in cls._instances
                 if inst is not instance}
    return min(set(range(len(positions) + 1)).difference(positions))
_free_pos._tqdm_314compat = True  # introspection marker


def _source_buggy(method):
    try:
        return "arg is an empty sequence" in inspect.getsource(method.__func__)
    except (OSError, TypeError, ValueError):
        return False


def _patch(tqdm_mod):
    cls = getattr(tqdm_mod, "tqdm", None)
    method = getattr(cls, "_get_free_pos", None)
    if method is None or not _source_buggy(method):
        return
    cls._get_free_pos = classmethod(_free_pos)


class _TqdmCompatFinder:
    def find_spec(self, fullname, path=None, target=None):
        if fullname != "tqdm":
            return None
        sys.meta_path.remove(self)
        try:
            spec = importlib.util.find_spec(fullname)
        finally:
            sys.meta_path.insert(0, self)
        if spec is None:
            return None
        if "tqdm" in sys.modules:  # already fully imported; patch directly
            _patch(sys.modules["tqdm"])
            return spec
        if spec.loader is None:
            return spec
        real_exec = spec.loader.exec_module

        def exec_module(module):
            real_exec(module)
            _patch(module)
        spec.loader.exec_module = exec_module
        return spec


try:
    sys.meta_path.insert(0, _TqdmCompatFinder())
except Exception:
    pass
