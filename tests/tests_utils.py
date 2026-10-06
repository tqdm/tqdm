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


def test_callback_io_wrapper_counts_bytes():
    from array import array
    from io import BytesIO

    from tqdm.utils import CallbackIOWrapper

    # A non-byte-format memoryview reports its element count from len()
    # but writes nbytes to the stream; the callback must see the bytes.
    stream = BytesIO()
    counts = []
    writer = CallbackIOWrapper(counts.append, stream, "write")
    wrote = writer.write(memoryview(array("I", [1, 2, 3])))
    assert wrote == 12
    assert len(stream.getvalue()) == 12
    assert counts == [12]

    # Plain bytes keep reporting their length.
    stream2 = BytesIO()
    counts2 = []
    writer2 = CallbackIOWrapper(counts2.append, stream2, "write")
    assert writer2.write(b"abcdefgh") == 8
    assert counts2 == [8]

    # Streams whose write() returns no count fall back to the data size.
    class NoCountStream:
        def __init__(self):
            self.buf = bytearray()

        def write(self, data):
            self.buf += data
            return None

    stream3 = NoCountStream()
    counts3 = []
    writer3 = CallbackIOWrapper(counts3.append, stream3, "write")
    assert writer3.write(memoryview(array("I", [1, 2, 3]))) is None
    assert len(stream3.buf) == 12
    assert counts3 == [12]
