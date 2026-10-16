"""
Tests for the optional OSC 7501 "Program Status Protocol" reporting
(`tqdm(..., program_status='myapp')`).

See https://github.com/tqdm/tqdm/issues/1873
"""
import re

from pytest import fixture, raises

from tqdm import tqdm
from tqdm.std import _program_status_progress, _program_status_seq

# `OSC 7501 ; <pairs> ST`
RE_OSC = re.compile(r"\x1b\]7501;([^\x1b]*)\x1b\\")
APP = 'myapp'


def oscs(text):
    """List of the OSC 7501 reports (`key=value` pairs joined by ':') in `text`"""
    return RE_OSC.findall(text)


def pairs(osc):
    """Dict of the `key=value` pairs in one OSC 7501 report"""
    return dict(p.split('=', 1) for p in osc.split(':'))


@fixture
def tty(tmp_file):
    """A writable stream which claims to be a tty"""
    tmp_file.isatty = lambda: True
    yield tmp_file


def test_program_status_encoder():
    """OSC 7501 sequence structure, base64 `msg` and no control characters"""
    assert _program_status_seq('working', APP) == '\x1b]7501;state=working:app=myapp\x1b\\'
    assert _program_status_seq('done', APP, progress=100) == (
        '\x1b]7501;state=done:app=myapp:progress=100\x1b\\')
    assert _program_status_seq('error', APP, record_id='3') == (
        '\x1b]7501;state=error:app=myapp:id=3\x1b\\')
    out = _program_status_seq('working', APP, msg='héllo\nworld')
    # `pairs()` takes a report body (`oscs()` output), i.e. without the OSC/ST framing
    assert pairs(oscs(out)[0]) == {'state': 'working', 'app': APP, 'msg': 'aMOpbGxvCndvcmxk'}
    assert all(ord(c) >= 32 or c == '\x1b' for c in out)


def test_program_status_progress():
    """`progress` is an integer 0-100, or None when `total` is unknown"""
    assert _program_status_progress(0, 4) == 0
    assert _program_status_progress(1, 3) == 33
    assert _program_status_progress(1, 1000) == 0
    assert _program_status_progress(9, 4) == 100  # clamped
    assert _program_status_progress(0, 0) is None
    assert _program_status_progress(0, None) is None


def test_program_status_working_done(tty):
    """`state=working` on the first display, `state=done` on normal exit"""
    with tqdm(total=4, file=tty, mininterval=0, miniters=1, program_status=APP) as t:
        assert oscs(tty.getvalue()) == ['state=working:app=myapp:progress=0']
        t.update(2)
    assert oscs(tty.getvalue()) == [
        'state=working:app=myapp:progress=0',
        'state=working:app=myapp:progress=50',
        'state=done:app=myapp']


def test_program_status_throttle(tty):
    """`state=working` only when the integer percentage changes"""
    with tqdm(total=1000, file=tty, mininterval=0, miniters=1, program_status=APP) as t:
        t.update(5)  # 0.5% => still 0%
        assert oscs(tty.getvalue()) == ['state=working:app=myapp:progress=0']
        t.update(5)  # 1.0% => 1%
        assert oscs(tty.getvalue())[-1] == 'state=working:app=myapp:progress=1'
        t.update(5)  # 1.5% => still 1%
        t.refresh()  # no progress change
        assert len(oscs(tty.getvalue())) == 2


def test_program_status_unknown_total(tty):
    """Unknown `total` => `state=working` with no `progress` key, once"""
    with tqdm(file=tty, mininterval=0, miniters=1, program_status=APP) as t:
        assert oscs(tty.getvalue()) == ['state=working:app=myapp']
        t.update()
        assert oscs(tty.getvalue()) == ['state=working:app=myapp']
    assert oscs(tty.getvalue()) == ['state=working:app=myapp', 'state=done:app=myapp']


def test_program_status_error(tty):
    """An escaping exception => `state=error`, never both `done` and `error`"""
    with raises(ZeroDivisionError):
        with tqdm(total=4, file=tty, mininterval=0, miniters=1, program_status=APP) as t:
            t.update(2)
            raise ZeroDivisionError("boom")
    assert oscs(tty.getvalue()) == [
        'state=working:app=myapp:progress=0',
        'state=working:app=myapp:progress=50',
        'state=error:app=myapp']


def test_program_status_nested(tty):
    """Nested (`position=`) bars report a child (`id`) record"""
    with tqdm(total=4, file=tty, mininterval=0, miniters=1, program_status=APP,
              position=1) as t:
        t.update(2)
    assert oscs(tty.getvalue()) == [
        'state=working:app=myapp:id=1:progress=0',
        'state=working:app=myapp:id=1:progress=50',
        'state=done:app=myapp:id=1']


def test_program_status_none(tmp_file):
    """Nothing is emitted when `program_status` is not set"""
    with tqdm(total=4, file=tmp_file, mininterval=0, miniters=1) as t:
        t.update(2)
    assert oscs(tmp_file.getvalue()) == []
    assert tmp_file.getvalue() != ''  # the bar itself still renders


def test_program_status_not_tty(tmp_file):
    """Nothing is emitted when the stream is not a tty"""
    assert not tmp_file.isatty()
    with tqdm(total=4, file=tmp_file, mininterval=0, miniters=1, program_status=APP) as t:
        t.update(2)
    assert oscs(tmp_file.getvalue()) == []
    assert tmp_file.getvalue() != ''


def test_program_status_disabled(tty):
    """Nothing is emitted for a disabled bar"""
    with tqdm(total=4, file=tty, disable=True, program_status=APP) as t:
        t.update(2)
    assert oscs(tty.getvalue()) == []


def test_program_status_invalid_app(tty):
    """An app name outside the protocol's value charset is rejected"""
    with raises(ValueError, match="program_status"):
        tqdm(file=tty, program_status='bad:app')
