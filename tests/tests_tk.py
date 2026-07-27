"""Test `tqdm.tk`."""
import os
import sys

from .tests_tqdm import importorskip, mark, skip


def test_tk_import():
    """Test `tqdm.tk` import"""
    importorskip('tqdm.tk')


@mark.filterwarnings("ignore:GUI is experimental/alpha:"
                     "tqdm.std.TqdmExperimentalWarning")
def test_tk_reset_inf_total():
    """Test `tqdm.tk` `reset(total=inf)` gives an indeterminate bar"""
    tk = importorskip('tqdm.tk')
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        skip("no DISPLAY")

    with tk.tqdm(total=10) as t:
        t.reset(total=float("inf"))
        assert t.total is None
        assert t._tk_pbar['maximum'] == 100
        assert str(t._tk_pbar['mode']) == "indeterminate"
