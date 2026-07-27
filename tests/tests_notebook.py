from tqdm.notebook import tqdm as tqdm_notebook

from .tests_tqdm import importorskip


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_reset_inf_total():
    """Test that reset(total=inf) gives an info style bar, as in __init__"""
    importorskip('ipywidgets')
    with tqdm_notebook(total=10) as t:
        t.reset(total=float("inf"))
        assert t.total is None
        _, pbar, _ = t.container.children
        assert pbar.max == 1
        assert pbar.bar_style == 'info'
        assert pbar.layout.width == "20px"
