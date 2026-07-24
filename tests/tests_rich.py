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
    assert not err
    assert '5/?' in out


def test_rich_fraction_column_no_total():
    """Test `FractionColumn` renders a `?` placeholder when total is unknown"""
    rich = importorskip('tqdm.rich')

    class Task:
        completed = 5
        total = None

    assert rich.FractionColumn().render(Task()).plain == "5/? "

    class SizedTask:
        completed = 3
        total = 10

    assert rich.FractionColumn().render(SizedTask()).plain == "3/10 "
