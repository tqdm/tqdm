"""Test `tqdm.__version__`."""
from ast import literal_eval
import re

from .tests_tqdm import pretest_posttest  # NOQA, pylint: disable=unused-import


def test_version():
    """Test version string"""
    from tqdm import __version__
    version_parts = re.split('[.-]', __version__)
    if __version__ != "UNKNOWN":
        assert 3 <= len(version_parts), "must have at least Major.minor.patch"
        assert all([isinstance(literal_eval(i), int)
                    for i in version_parts[:3]]), (
            "Version Major.minor.patch must be 3 integers")
