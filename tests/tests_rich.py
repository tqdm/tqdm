"""Test `tqdm.rich`."""
from pytest import importorskip, mark


@mark.filterwarnings("ignore:rich is experimental/alpha:"
                     "tqdm.std.TqdmExperimentalWarning")
def test_rich_no_total(capsys):
    """Test `tqdm.rich` on an iterable without a length, e.g. a generator"""
    rich = importorskip('tqdm.rich')
    with rich.tqdm(i for i in range(5)) as pbar:
        for _ in pbar:
            pass
    out, err = capsys.readouterr()
    assert not out
    assert '5it' in err


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
