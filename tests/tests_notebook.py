from types import SimpleNamespace

import tqdm.notebook as notebook
from tqdm.notebook import tqdm as tqdm_notebook


def _dummy_container():
    layout = SimpleNamespace(
        width=None, display=None, flex_flow=None, visibility=None, flex=None)
    progress = SimpleNamespace(
        value=0, bar_style='', layout=layout,
        style=SimpleNamespace(bar_color=None))
    container = SimpleNamespace(
        children=[
            SimpleNamespace(value=""),
            progress,
            SimpleNamespace(value=""),
        ],
        layout=layout,
        visible=True,
        pbar=None,
    )
    container.close = lambda: setattr(container, 'visible', False)
    return container


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_update_returns_none(monkeypatch):
    monkeypatch.setattr(
        tqdm_notebook, 'status_printer',
        staticmethod(lambda *args, **kwargs: _dummy_container()),
    )
    monkeypatch.setattr(notebook, 'display', lambda *args, **kwargs: None, raising=False)

    with tqdm_notebook(total=2, display=False, mininterval=0, miniters=1) as t:
        assert t.update() is None
