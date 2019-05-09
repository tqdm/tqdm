"""
Itertools wrappers that know about their length if possible
"""

import functools as _functools
import itertools as _itertools
import operator as _operator
from itertools import *


class _Base:
    # Subclasses must define _base_iterator and _get_length.

    def __init__(self, *args, **kwargs):
        self._iterator = type(self)._base_iterator(*args, **kwargs)
        try:
            self._length = type(self)._get_length(*args, **kwargs)
        except TypeError:
            self._length = None

    def __iter__(self):
        return self._iterator

    def __len__(self):
        return self._length


class zip(_Base):
    _base_iterator = zip

    @staticmethod
    def _get_length(*args):
        return min(map(len, args))


class product(_Base):
    _base_iterator = _itertools.product

    @staticmethod
    def _get_length(*args, repeat=1):
        return _functools.reduce(_operator.mul, map(len, args)) ** repeat


class zip_longest(_Base):
    _base_iterator = zip_longest

    @staticmethod
    def _get_length(*args):
        return max(map(len, args))
