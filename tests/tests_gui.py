"""Test `tqdm.gui`."""
from .tests_tqdm import importorskip


def test_gui_import():
    """Test `tqdm.gui` import"""
    importorskip('tqdm.gui')
