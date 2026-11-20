import pytest

from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_ncols_number_is_characters():
    """Test that a numeric ncols is a width in characters, as in std tqdm (#1927)"""
    pytest.importorskip("ipywidgets")
    for ncols, width in ((79, "79ch"), ("79", "79ch"), ("480px", "480px"), ("100%", "100%")):
        container = tqdm_notebook.status_printer(None, total=10, ncols=ncols)
        assert container.layout.width == width
