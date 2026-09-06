from pytest import importorskip


def test_tk_import():
    importorskip('tqdm.tk')
