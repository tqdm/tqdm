# How to import tqdm without enforcing it as a dependency
try:
    from tqdm import tqdm
except:
    def tqdm(*args, **kwargs):
        if args:
            return args[0]
        return kwargs.get('iterable', None)
