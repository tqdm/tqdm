from __future__ import division

from time import sleep

from .tests_tqdm import importorskip, mark

pytestmark = mark.slow


def test_dask(capsys):
    """Test tqdm.dask.TqdmCallback"""
    ProgressBar = importorskip('tqdm.dask').TqdmCallback
    dask = importorskip('dask')

    schedule = [dask.delayed(sleep)(i / 10) for i in range(5)]
    with ProgressBar(desc="computing"):
        dask.compute(schedule)
    _, err = capsys.readouterr()
    assert "computing: " in err
    assert '5/5' in err
