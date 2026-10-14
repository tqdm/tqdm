from ast import literal_eval
from collections import defaultdict
from typing import Union  # py<3.10

from pytest import warns

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


def test_callbackio_write_reports_stream_count():
    from io import BytesIO
    from array import array

    from tqdm.utils import CallbackIOWrapper

    stream = BytesIO()
    counts = []
    wrapper = CallbackIOWrapper(counts.append, stream, 'write')

    data = memoryview(array('I', [1, 2, 3]))
    assert wrapper.write(data) == len(data) * data.itemsize
    assert counts == [stream.tell()]


def test_callbackio_write_falls_back_to_input_length():
    from io import StringIO

    from tqdm.utils import CallbackIOWrapper

    class NoCount(StringIO):
        def write(self, data):
            self.written = data
            return None

    stream = NoCount()
    counts = []
    wrapper = CallbackIOWrapper(counts.append, stream, 'write')

    assert wrapper.write("hello") is None
    assert counts == [5]
