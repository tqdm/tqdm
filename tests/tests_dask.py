from time import sleep

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
