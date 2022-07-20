# How to import tqdm in any frontend without enforcing it as a dependency
try:
    from tqdm.auto import tqdm
except ImportError:

    def tqdm(*args, **kwargs):
        if args:
            return args[0]
        return kwargs.get('iterable', None)

__all__ = ['tqdm']
