from ast import literal_eval
from collections import defaultdict
from typing import Union  # py<3.10

from pytest import mark, warns

from tqdm.utils import envwrap, strip_control_sequences


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
    def annotated(number: int | float = None, string: int = None):
        return number, string

    assert 1.1, "1.1" == annotated()


@mark.parametrize('src, expected', [
    # OSC 52 clipboard write, BEL- and ST-terminated
    ("\x1b]52;c;cGF5bG9hZA==\x07", ""),
    ("\x1b]52;c;cGF5bG9hZA==\x1b\\", ""),
    # OSC 0 window title
    ("\x1b]0;evil\x1b\\", ""),
    # OSC 8 hyperlink: sequence goes, link text stays
    ("\x1b]8;;http://example.com\x1b\\link\x1b]8;;\x1b\\", "link"),
    # cursor/erase CSI sequences
    ("\x1b[2J\x1b[3J", ""),
    ("\x1b[1;1Hmoved", "moved"),
    # SGR colour is preserved
    ("\x1b[31mred\x1b[0m", "\x1b[31mred\x1b[0m"),
    # C0 controls other than \t \n \r are dropped
    ("a\x07b\x08c", "abc"),
    # \t \n \r survive
    ("a\tb\nc\rd", "a\tb\nc\rd"),
    # a lone ESC is dropped
    ("a\x1bb", "ab"),
    # non-strings pass through untouched
    (None, None),
])
def test_strip_control_sequences(src, expected):
    """Untrusted descriptions must not be able to drive the terminal."""
    assert strip_control_sequences(src) == expected
