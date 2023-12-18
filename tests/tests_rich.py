"""Test `tqdm.rich`."""
from .tests_tqdm import importorskip


def test_rich_import():
    """Test `tqdm.rich` import"""
    importorskip('tqdm.rich')
