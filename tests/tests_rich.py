"""Test `tqdm.rich`."""
from contextlib import closing
from io import StringIO

from pytest import mark

from .tests_tqdm import importorskip


def test_rich_import():
    """Test `tqdm.rich` import"""
    importorskip('tqdm.rich')


@mark.filterwarnings("ignore:rich is experimental/alpha:"
                     "tqdm.std.TqdmExperimentalWarning")
def test_rich_no_total():
    """Test `tqdm.rich` on an iterable without a length, e.g. a generator"""
    rich = importorskip('tqdm.rich')
    with closing(StringIO()) as our_file:
        # a generator has no __len__, so the rich task total stays None
        with rich.tqdm((i for i in range(5)), file=our_file) as pbar:
            for _ in pbar:
                pass


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
