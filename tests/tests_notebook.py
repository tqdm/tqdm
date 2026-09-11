from pytest import importorskip, mark

from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


@mark.parametrize("ncols", ["100%", "480px"])
@mark.parametrize("bar_format", [None, "{l_bar}{bar:20}{r_bar}"])
def test_notebook_css_width(ncols, bar_format):
    """CSS widths must not be used as character counts in text representations."""
    importorskip("ipywidgets")
    pretty = importorskip("IPython.lib.pretty").pretty
    with tqdm_notebook(total=4, ncols=ncols, bar_format=bar_format, display=False) as t:
        assert "0/4" in repr(t.container)
        t.update(2)
        t.refresh()
        assert "2/4" in str(t)
        assert "2/4" in repr(t.container)
        assert "2/4" in pretty(t.container)
        if hasattr(t.container, "_repr_mimebundle_"):
            assert "2/4" in t.container._repr_mimebundle_()["text/plain"]
        assert t.container.children[1].value == 2
        assert t.ncols == ncols
        assert t.container.layout.width == ncols
    assert t.container.layout.width == ncols


@mark.parametrize("ncols", [None, 0, 80])
def test_notebook_numeric_width(ncols):
    """Keep existing text formatting for numeric and unspecified widths."""
    importorskip("ipywidgets")
    with tqdm_notebook(total=4, ncols=ncols, display=False) as t:
        assert t.format_dict["ncols"] == ncols
        text = repr(t.container)
        assert "0/4" in text
        if ncols:
            assert len(text) == ncols
            assert t.container.layout.width == f"{ncols}px"
        elif ncols == 0:
            assert "|" not in text
