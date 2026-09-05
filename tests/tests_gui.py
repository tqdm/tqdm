from pytest import importorskip


def test_gui_import():
    importorskip('tqdm.gui')
