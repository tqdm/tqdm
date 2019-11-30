from tqdm import tqdm
from tqdm.utils import ObjectWrapper


class DummyTqdmFile(ObjectWrapper):
    """Dummy file-like that will write to tqdm"""
    def write(self, x, nolock=False):
        # Avoid print() second call (useless \n)
        if len(x.rstrip()) > 0:
            tqdm.write(x, file=self._wrapped, nolock=nolock)
