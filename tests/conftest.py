import sys
from io import StringIO

from pytest import fixture, importorskip, skip

from tqdm import tqdm


def _assert_no_instances(when):
    if instances := getattr(tqdm, '_instances', None):
        n = len(instances)
        instances.clear()
        raise OSError(f"{n} `tqdm` instances still in existence {when}-test")


@fixture(autouse=True)
def pretest_posttest():
    """Ensure environment cleanup around every test"""
    sys.setswitchinterval(1)
    _assert_no_instances("PRE")
    yield
    _assert_no_instances("POST")


@fixture
def caperr(capsys):
    """shortcut for `capsys.readouterr().err` (and `assert not out`)"""
    def inner():
        out, err = capsys.readouterr()
        assert not out, f"Expected no stdout, got: {out}"
        return err
    yield inner


@fixture
def tmp_file():
    """Writable in-memory text stream"""
    with StringIO() as file:
        yield file


@fixture
def tmp_file2():
    """Second `tmp_file`, e.g. to separate two bars' output"""
    with StringIO() as file:
        yield file


def _patch_lock(module):
    """Swap tqdm's lock for a vanilla `RLock`, restoring it afterwards"""
    try:
        lock = importorskip(module).RLock()
    except OSError as err:  # e.g. no /dev/shm
        skip(str(err))
    default_lock = tqdm.get_lock()
    tqdm.set_lock(lock)
    yield lock
    tqdm.set_lock(default_lock)


@fixture
def thread_lock():
    """`threading.RLock` as tqdm's lock"""
    yield from _patch_lock('threading')


@fixture
def process_lock():
    """`multiprocessing.RLock` as tqdm's lock"""
    yield from _patch_lock('multiprocessing')
