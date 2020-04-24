from __future__ import print_function
from os import path
import sys
sys.path.insert(0, path.dirname(path.dirname(__file__)))  # NOQA
import tqdm
import tqdm.cli
from io import open as io_open
from os import path

src_dir = path.abspath(path.dirname(__file__))
completion = u"""\
#!/usr/bin/env bash

# TODO: programatically generate based on tqdm.tqdm/tqdm.cli
"""

if __name__ == "__main__":
    fncompletion = path.join(path.dirname(src_dir), 'tqdm', 'completion.sh')
    with io_open(fncompletion, mode='w', encoding='utf-8') as fd:
        fd.write(completion)
