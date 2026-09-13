"""Test `tqdm.rich`."""
from pytest import importorskip, mark


@mark.filterwarnings("ignore:rich is experimental/alpha:tqdm.std.TqdmExperimentalWarning")
def test_rich_no_total(capsys):
    """Test `tqdm.rich` on an iterable without a length, e.g. a generator"""
    rich = importorskip('tqdm.rich')
    with rich.tqdm(i for i in range(5)) as pbar:
        for _ in pbar:
            pass
    out, err = capsys.readouterr()
    assert not out
    assert '5it' in err


@mark.filterwarnings("ignore:rich is experimental/alpha:"
                     "tqdm.std.TqdmExperimentalWarning")
def test_rich_ascii(capsys):
    """Test `trrange` with `ascii=True`, i.e. rendering via `ASCIIConsole`"""
    rich = importorskip('tqdm.rich')
    with rich.trange(3, ascii=True, ncols=60) as pbar:
        assert list(pbar) == [0, 1, 2]
    out, err = capsys.readouterr()
    assert not out
    assert err.isascii()
    assert '---' in err


def test_rich_fraction_column():
    """Test `FractionColumn` for different totals & unit scaling"""
    rich = importorskip('tqdm.rich')

    class Task:
        completed = 5
        total = None

    assert str(rich.FractionColumn().render(Task())) == ""

    class SizedTask:
        def __init__(self, **fields):
            self.fields = fields
        completed = 3
        total = 1000

    assert str(rich.FractionColumn().render(SizedTask(unit_scale=False))) == "3/1000"
    assert str(rich.FractionColumn().render(SizedTask(
        unit_scale=True, unit_divisor=1000))) == "3.00/1.00k"


def test_rich_rate_column():
    """Test `RateColumn` fallback, derivation, inversion"""
    rich = importorskip('tqdm.rich')

    class Task:
        def __init__(self, **fields):
            self.fields = dict(
                {'unit': 'it', 'unit_scale': False, 'rate': None, 'elapsed': 0}, **fields)
        completed = 10

    assert str(rich.RateColumn().render(Task())) == "?it/s"
    assert str(rich.RateColumn().render(Task(elapsed=5))) == " 2.00it/s"
    assert str(rich.RateColumn().render(Task(rate=0.5))) == " 2.00s/it"


def test_rich_completed_column():
    """Test `UnitCompletedColumn` with total shows percentage."""
    rich = importorskip('tqdm.rich')

    class SizedTask:
        percentage = 75.0
        total = 4

    assert str(rich.UnitCompletedColumn().render(SizedTask())) == " 75%"
