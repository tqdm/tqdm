from ast import literal_eval
from collections import defaultdict
from typing import Union  # py<3.10

from pytest import warns

from tqdm.utils import disp_len
from tqdm.utils import disp_trim
from tqdm.utils import envwrap


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


# OSC 8 hyperlink, terminated by ST (ESC \)
_OSC8_LINK = "\x1b]8;;https://example.com\x1b\\docs\x1b]8;;\x1b\\"


def test_disp_len_ignores_osc_sequences():
    # An OSC 8 hyperlink is zero-width; only the visible label counts (#1856).
    assert disp_len(_OSC8_LINK) == 4
    # A BEL-terminated OSC sequence (e.g. OSC 52 clipboard) is also zero-width.
    assert disp_len("\x1b]52;c;Zm9v\x07visible") == 7
    # Plain CSI colour codes keep working.
    assert disp_len("\x1b[31mhello\x1b[0m") == 5


def test_disp_trim_does_not_cut_osc_sequences():
    # Trimming to the label's width must not split an escape sequence (#1856).
    trimmed = disp_trim(_OSC8_LINK, 4)
    assert _OSC8_LINK in trimmed
    assert disp_len(trimmed) == 4
