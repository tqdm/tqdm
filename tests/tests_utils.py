from ast import literal_eval
from collections import defaultdict
from typing import Union  # py<3.10

from pytest import mark, warns

from tqdm.utils import disp_len, disp_trim, envwrap


@mark.parametrize('terminator', ['\x1b\\', '\x07'])
@mark.parametrize('params', ['', 'id=docs'])
def test_hyperlink_width_and_trimming(terminator, params):
    start = f'\x1b]8;{params};https://example.com/a;b{terminator}'
    end = f'\x1b]8;;{terminator}'
    link = start + 'docs' + end

    assert disp_len(link) == 4
    assert disp_trim(link, 0) == start + end
    assert disp_trim(link, 4) == link
    assert disp_trim(link, 3) == start + 'doc' + end
    assert disp_trim('a ' + link + ' z', 6) == 'a ' + link
    assert disp_trim('a ' + link + ' z', 7) == 'a ' + link + ' '


@mark.parametrize('terminator', ['\x1b\\', '\x07'])
def test_hyperlink_trimming_wide_and_coloured_text(terminator):
    start = f'\x1b]8;;https://example.com{terminator}'
    end = f'\x1b]8;;{terminator}'
    link = start + '\x1b[31m日本語\x1b[0m' + end

    assert disp_len(link) == 6
    assert disp_trim(link, 3) == start + '\x1b[31m日' + end + '\x1b[0m'
    assert disp_len(disp_trim(link, 3)) == 2


@mark.parametrize('terminator', ['\x1b\\', '\x07'])
def test_hyperlink_trimming_equal_raw_and_visible_lengths(terminator):
    start = f'\x1b]8;;https://example.com{terminator}'
    end = f'\x1b]8;;{terminator}'
    link = start + '日' * (len(start) + len(end)) + end

    assert len(link) == disp_len(link)
    assert disp_trim(link, 4) == start + '日日' + end


def test_hyperlink_trimming_multiple_links():
    first = '\x1b]8;;https://example.com/first\x1b\\'
    second = '\x1b]8;;https://example.com/second\x07'
    end = '\x1b]8;;\x07'

    assert disp_trim(first + 'one' + second + 'two' + end, 4) == (
        first + 'one' + second + 't' + end)


def test_hyperlink_trimming_before_link():
    link = '\x1b]8;;https://example.com\x07docs\x1b]8;;\x07'
    assert disp_trim('before ' + link, 3) == 'bef'


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
