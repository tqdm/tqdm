"""Test `tqdm.tk`."""
from .tests_tqdm import importorskip


def test_tk_import():
    """Test `tqdm.tk` import"""
    importorskip('tqdm.tk')
