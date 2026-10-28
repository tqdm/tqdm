from ast import literal_eval
from collections import defaultdict
from typing import Union  # py<3.10

from pytest import warns

from tqdm.utils import disp_escape, disp_len, disp_trim, envwrap


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


def test_disp_len_escapes():
    assert 4 == disp_len("docs")
    # OSC 8 hyperlinks, BEL- and ST-terminated
    assert 4 == disp_len("\x1b]8;;https://example.com\x1b\\docs\x1b]8;;\x1b\\")
    assert 4 == disp_len("\x1b]8;;https://example.com\x07docs\x1b]8;;\x07")
    # window title (OSC) and non-SGR CSI are nonprinting too
    assert 0 == disp_len("\x1b]0;title\x07")
    assert 0 == disp_len("\x1b[2K\x1b[1;1H")
    assert 3 == disp_len("\x1b[31mred\x1b[0m")


def test_disp_trim_keeps_sequences_whole():
    link = "\x1b]8;;https://example.com\x1b\\docs\x1b]8;;\x1b\\"
    assert link == disp_trim(link, 4)
    assert "\x1b]8;;https://example.com\x1b\\do\x1b]8;;\x1b\\" == disp_trim(link, 2)
    assert "\x1b[31mabc\x1b[0m" == disp_trim("\x1b[31mabcdef\x1b[0m", 3)
    assert "abc" == disp_trim("abcdef", 3)
    assert "\u4f60\u597d" == disp_trim("\u4f60\u597d\u4e16\u754c", 4)


def test_disp_escape():
    # SGR (colour) is the only escape forwarded untouched
    assert "\x1b[31mred\x1b[0m" == disp_escape("\x1b[31mred\x1b[0m")
    # everything else is made visible instead of being executed
    assert "^[]0;title^G" == disp_escape("\x1b]0;title\x07")
    assert "^[[2Knext" == disp_escape("\x1b[2Knext")
    assert "bell^G" == disp_escape("bell\x07")
    assert "^A" == disp_escape("\x01")
    # newlines and tabs survive (multi-line messages)
    assert "a\nb\tc" == disp_escape("a\nb\tc")
    assert "plain text" == disp_escape("plain text")
    assert "" == disp_escape("")
