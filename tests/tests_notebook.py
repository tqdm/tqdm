from pytest import importorskip

from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")



def test_notebook_numeric_ncols_uses_character_width():
    importorskip('ipywidgets')

    container = tqdm_notebook.status_printer(None, total=100, ncols=79)

    assert container.layout.width == '79ch'


def test_notebook_css_ncols_are_preserved():
    importorskip('ipywidgets')

    for ncols in ('100px', '100%'):
        container = tqdm_notebook.status_printer(None, total=100, ncols=ncols)
        assert container.layout.width == ncols
