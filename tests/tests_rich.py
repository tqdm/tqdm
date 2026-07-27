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


@mark.filterwarnings("ignore:rich is experimental/alpha:"
                     "tqdm.std.TqdmExperimentalWarning")
def test_rich_reset():
    """Test `tqdm.rich` reset(), including `total=inf` meaning unknown"""
    rich = importorskip('tqdm.rich')
    with rich.tqdm(total=10, desc="desc") as pbar:
        pbar.update(5)
        pbar.reset(total=20)
        task = pbar._prog.tasks[0]
        assert (pbar.total, task.total, task.completed) == (20, 20, 0)

        pbar.reset(total=float("inf"))
        task = pbar._prog.tasks[0]
        assert pbar.total is None
        assert task.total is None  # indeterminate, as in `__init__`
        assert task.description == "desc"


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
