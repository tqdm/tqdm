from ast import literal_eval
from collections import defaultdict
from typing import Union  # py<3.10

from tqdm.utils import envwrap


def test_envwrap(monkeypatch):
    """Test @envwrap (basic)"""
    monkeypatch.setenv('FUNC_A', "42")
    monkeypatch.setenv('FUNC_TyPe_HiNt', "1337")
    monkeypatch.setenv('FUNC_Unused', "x")

    @envwrap("FUNC_")
    def func(a=1, b=2, type_hint: int = None):
        return a, b, type_hint

    assert (42, 2, 1337) == func()
    assert (99, 2, 1337) == func(a=99)


def test_envwrap_types(monkeypatch):
    """Test @envwrap(types)"""
    monkeypatch.setenv('FUNC_notype', "3.14159")

    @envwrap("FUNC_", types=defaultdict(lambda: literal_eval))
    def func(notype=None):
        return notype

    assert 3.14159 == func()

    monkeypatch.setenv('FUNC_number', "1")
    monkeypatch.setenv('FUNC_string', "1")

    @envwrap("FUNC_", types={'number': int})
    def nofallback(number=None, string=None):
        return number, string

    assert 1, "1" == nofallback()


def test_envwrap_annotations(monkeypatch):
    """Test @envwrap with typehints"""
    monkeypatch.setenv('FUNC_number', "1.1")
    monkeypatch.setenv('FUNC_string', "1.1")

    @envwrap("FUNC_")
    def annotated(number: Union[int, float] = None, string: int = None):
        return number, string

    assert 1.1, "1.1" == annotated()
