from ast import literal_eval
from collections import defaultdict
from typing import Union  # py<3.10

from pytest import warns

from tqdm.utils import _is_ascii, _text_width, disp_len, disp_trim, envwrap


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


def test_disp_len_and_trim():
    assert _is_ascii("")
    assert _is_ascii("abc 123")
    assert _is_ascii("caf\xe9")
    assert not _is_ascii("\u2588")

    # ASCII and Bar.UTF block elements have width 1 per character
    blocks = "\u2588\u2589\u258a\u258b\u258c\u258d\u258e\u258f"
    assert _text_width("abc") == 3
    assert _text_width(blocks) == len(blocks)
    assert disp_len("50%|" + blocks + "| 1/2") == 4 + len(blocks) + 5

    # Fullwidth / CJK characters count as width 2
    assert disp_len("\uff41\uff42c") == 5
    assert disp_trim("\uff41\uff42c", 5) == "\uff41\uff42c"
    assert disp_trim("\uff41\uff42c", 4) == "\uff41\uff42"
    assert disp_trim("\uff41\uff42c", 3) == "\uff41"

    # ANSI escape codes have zero display width and get a reset when present
    colored = "\x1b[32mhello\x1b[0m world"
    assert disp_len(colored) == 11
    assert disp_trim(colored, 11) == colored + "\x1b[0m"
    assert disp_trim(colored, 4) == "\x1b[32mhell\x1b[0m"
    assert disp_trim("abc\x1b[32m", 2) == "ab"
