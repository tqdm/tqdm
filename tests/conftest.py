"""Shared pytest config."""
import sys

from pytest import fixture

from tqdm import tqdm


@fixture(autouse=True)
def pretest_posttest():
    """Fixture for all tests ensuring environment cleanup"""
    try:
        sys.setswitchinterval(1)
    except AttributeError:
        sys.setcheckinterval(100)  # deprecated

    if getattr(tqdm, "_instances", False):
        n = len(tqdm.__instances__)
        if n:
            tqdm.__instances__.clear()
            raise OSError(f"{n} `tqdm` instances still in existence PRE-test")
    yield
    if getattr(tqdm, "_instances", False):
        n = len(tqdm.__instances__)
        if n:
            tqdm.__instances__.clear()
            raise OSError(f"{n} `tqdm` instances still in existence POST-test")
