"""An example of wrapping manual tqdm updates for urllib reporthook.

# urllib.urlretrieve documentation
> If present, the hook function will be called once
> on establishment of the network connection and once after each block read
> thereafter. The hook will be passed three arguments; a count of blocks
> transferred so far, a block size in bytes, and the total size of the file.

Usage:
    tqdm_wget.py [options]

Options:
-h, --help
    Print this help message and exit
-u URL, --url URL  : string, optional
    The url to fetch.
    [default: http://www.doc.ic.ac.uk/~cod11/matryoshka.zip]
-o FILE, --output FILE  : string, optional
    The local file path in which to save the url [default: /dev/null].
"""

import urllib
from tqdm import tqdm
from docopt import docopt


def my_hook(t):
    """
    Wraps tqdm instance. Don't forget to close() or __exit__()
    the tqdm instance once you're done with it (easiest using `with` syntax).

    Example
    -------

    >>> with tqdm(...) as t:
    ...     reporthook = my_hook(t)
    ...     urllib.urlretrieve(..., reporthook=reporthook)

    """
    last_b = [0]

    def inner(b=1, bsize=1, tsize=None):
        """
        b  : int, optional
            Number of blocks just transferred [default: 1].
        bsize  : int, optional
            Size of each block (in tqdm units) [default: 1].
        tsize  : int, optional
            Total size (in tqdm units). If [default: None] remains unchanged.
        """
        if tsize is not None:
            t.total = tsize
        t.update((b - last_b[0]) * bsize)
        last_b[0] = b
    return inner


opts = docopt(__doc__)

eg_link = opts['--url']
eg_file = eg_link.replace('/', ' ').split()[-1]
with tqdm(unit='B', unit_scale=True, leave=True, miniters=1,
          desc=eg_file) as t:  # all optional kwargs
    urllib.urlretrieve(eg_link, filename=opts['--output'],
                       reporthook=my_hook(t), data=None)
