import sys

if sys.version_info[:2] > (3, 6):
    from py37_asyncio import *  # NOQA
else:
    from unittest import SkipTest
    raise SkipTest
