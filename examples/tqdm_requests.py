"""An example of wrapping manual tqdm updates for `requests.get`.
See also: tqdm_wget.py.

Usage:
    tqdm_requests.py [options]

Options:
-h, --help
    Print this help message and exit
-u URL, --url URL  : string, optional
    The url to fetch.
    [default: https://caspersci.uk.to/matryoshka.zip]
-o FILE, --output FILE  : string, optional
    The local file path in which to save the url [default: /dev/null].
"""

from os import devnull

import requests
from docopt import docopt

from tqdm.auto import tqdm

opts = docopt(__doc__)

eg_link = opts['--url']
eg_file = eg_link.replace('/', ' ').split()[-1]
eg_out = opts['--output'].replace("/dev/null", devnull)

response = requests.get(eg_link, stream=True)
with open(eg_out, "wb") as fout:
    with tqdm(
        # all optional kwargs
        unit='B', unit_scale=True, unit_divisor=1024, miniters=1,
        desc=eg_file, total=int(response.headers.get('content-length', 0))
    ) as pbar:
        for chunk in response.iter_content(chunk_size=4096):
            fout.write(chunk)
            pbar.update(len(chunk))

# Even simpler progress by wrapping the output file's `write()`
response = requests.get(eg_link, stream=True)
with tqdm.wrapattr(
    open(eg_out, "wb"), "write",
    unit='B', unit_scale=True, unit_divisor=1024, miniters=1,
    desc=eg_file, total=int(response.headers.get('content-length', 0))
) as fout:
    for chunk in response.iter_content(chunk_size=4096):
        fout.write(chunk)
