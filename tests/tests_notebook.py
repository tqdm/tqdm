from pytest import importorskip

from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_desc_escaped(monkeypatch):
    """Test that desc is HTML-escaped before the widget is first displayed"""
    importorskip('ipywidgets')
    import tqdm.notebook as tqdm_nb
    shown = []
    monkeypatch.setattr(tqdm_nb, "display", lambda c: shown.append(c.children[0].value))
    with tqdm_notebook(1, desc="<b>&") as t:
        assert shown == ["&lt;b&gt;&amp;"]
        assert "<b>" not in t.container.children[0].value
