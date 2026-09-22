from time import sleep
from unittest.mock import Mock

from pytest import importorskip, mark

pytestmark = mark.slow


def test_dask(caperr):
    """Test tqdm.dask.TqdmCallback"""
    ProgressBar = importorskip('tqdm.dask').TqdmCallback
    dask = importorskip('dask')

    schedule = [dask.delayed(sleep)(i / 10) for i in range(5)]
    with ProgressBar(desc="computing"):
        dask.compute(schedule)
    err = caperr()
    assert "computing: " in err
    assert '5/5' in err


@mark.parametrize('tqdm_module', ['tqdm.std', 'tqdm.notebook'])
def test_dask_display(monkeypatch, tqdm_module):
    ProgressBar = importorskip('tqdm.dask').TqdmCallback
    dask = importorskip('dask')
    notebook = importorskip('tqdm.notebook')
    tqdm_class = importorskip(tqdm_module).tqdm
    display = Mock()
    monkeypatch.setattr(notebook, 'display', display)
    kwargs = {'display': False} if tqdm_module == 'tqdm.notebook' else {}
    callback = ProgressBar(tqdm_class=tqdm_class, **kwargs)

    with callback:
        dask.compute(dask.delayed(callback.display)(), scheduler='synchronous')

    if tqdm_module == 'tqdm.notebook':
        display.assert_called_once_with(callback.pbar.container)
    else:
        display.assert_not_called()
