from __future__ import unicode_literals

import csv

try:
    from StringIO import StringIO
except:
    from io import StringIO


def test_version():
    from tqdm import __version__
    assert len(__version__.split('.')) == 4
