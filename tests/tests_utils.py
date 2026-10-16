from ast import literal_eval
from collections import defaultdict
from typing import Union  # py<3.10
from unicodedata import normalize

from pytest import mark, warns

from tqdm import tqdm
from tqdm.utils import disp_len, disp_trim, envwrap


@mark.parametrize('text, width', [
    ('cafe\u0301', 4), ('a\u20dd', 1), ('好e\u0301', 3), ('か\u3099', 2),
    ('\x1b[31mcafe\u0301\x1b[0m', 4),
])
def test_disp_len_nonspacing_marks(text, width):
    assert disp_len(text) == width


@mark.parametrize('text, width, expected', [
    ('cafe\u0301XYZ', 4, 'cafe\u0301'),
    ('好e\u0301', 2, '好'),
    ('a\u20ddbc', 1, 'a\u20dd'),
    ('か\u3099a', 2, 'か\u3099'),
])
def test_disp_trim_nonspacing_marks(text, width, expected):
    assert disp_trim(text, width) == expected


def test_meter_canonical_equivalent_description():
    composed = tqdm.format_meter(1, 10, 1, ncols=60, prefix='café')
    decomposed = tqdm.format_meter(1, 10, 1, ncols=60, prefix='cafe\u0301')
    assert normalize('NFC', decomposed) == composed


def test_envwrap_deprecated(monkeypatch):
    monkeypatch.setenv('FUNC_A', "42")
    monkeypatch.setenv('FUNC_TyPe_HiNt', "1337")
    monkeypatch.setenv('FUNC_Unused', "x")

    with warns(DeprecationWarning, match="Trailing underscore in `name` is automatic"):
        @envwrap("FUNC_")
        def func(a=1, b=2, type_hint: int = None):
            return a, b, type_hint

    assert (42, 2, 1337) == func()
    assert (99, 2, 1337) == func(a=99)


def test_envwrap(monkeypatch):
    monkeypatch.setenv('NAME_FUNC_A', "42")
    monkeypatch.setenv('NAME_TyPe_HiNt', "1337")
    monkeypatch.setenv('NAME_unused', "x")

    @envwrap("name", "func")
    def func(a=1, b=2, type_hint: int = None):
        return a, b, type_hint

    assert (42, 2, 1337) == func()
    assert (99, 2, 1337) == func(a=99)


def test_envwrap_types(monkeypatch):
    monkeypatch.setenv('FUNC_notype', "3.14159")

    @envwrap("func", types=defaultdict(lambda: literal_eval))
    def func(notype=None):
        return notype

    assert 3.14159 == func()

    monkeypatch.setenv('FUNC_number', "1")
    monkeypatch.setenv('FUNC_string', "1")

    @envwrap("func", types={'number': int})
    def nofallback(number=None, string=None):
        return number, string

    assert 1, "1" == nofallback()


def test_envwrap_annotations(monkeypatch):
    monkeypatch.setenv('FUNC_number', "1.1")
    monkeypatch.setenv('FUNC_string', "1.1")

    @envwrap("func")
    def annotated(number: Union[int, float] = None, string: int = None):
        return number, string

    assert 1.1, "1.1" == annotated()
