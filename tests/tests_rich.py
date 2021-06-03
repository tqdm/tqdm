"""Test `tqdm.rich`."""
import sys

from .tests_tqdm import importorskip, mark


@mark.skipif(sys.version_info[:3] < (3, 6, 1), reason="`rich` needs py>=3.6.1")
def test_rich_import():
    """Test `tqdm.rich` import"""
    importorskip('tqdm.rich')
