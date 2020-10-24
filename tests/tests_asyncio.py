"""Tests `tqdm.asyncio` on `python>=3.7`."""
import sys

if sys.version_info[:2] > (3, 6):
    from .py37_asyncio import *  # NOQA, pylint: disable=wildcard-import
else:
    import pytest
    try:
        pytest.skip("async not supported", allow_module_level=True)
    except TypeError:
        pass
