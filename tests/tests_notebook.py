from pytest import importorskip

from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_bar_style_after_early_exit():
    importorskip('ipywidgets')
    with tqdm_notebook(range(10), display=False) as t:
        for _ in t:
            break
    pbar = t.container.children[1]
    assert pbar.bar_style == 'danger'
    t.bar_style = 'success'
    assert pbar.bar_style == 'success'
    assert t.bar_style == 'success'
    assert t.n < t.total


def test_notebook_bar_style_reset():
    importorskip('ipywidgets')
    with tqdm_notebook(total=10, display=False) as t:
        t.bar_style = 'warning'
        assert t.container.children[1].bar_style == 'warning'
        t.reset()
        assert t.bar_style == ''


def test_notebook_disabled_bar_style():
    with tqdm_notebook(total=10, disable=True) as t:
        assert t.bar_style is None
        t.bar_style = 'success'
        assert t.bar_style is None
