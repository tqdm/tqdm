# Advice: use repr(our_file.read()) to print the full output of tqdm
# (else '\r' will replace the previous lines and you'll see only the latest.

from __future__ import unicode_literals

import sys
import csv
import re
import os
from nose import with_setup
from nose.plugins.skip import SkipTest
from nose.tools import assert_raises
from contextlib import contextmanager

from tqdm import tqdm
from tqdm import trange
from tqdm import TqdmDeprecationWarning

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from io import IOBase  # to support unicode strings


class DeprecationError(Exception):
    pass


# Ensure we can use `with closing(...) as ... :` syntax
if getattr(StringIO, '__exit__', False) and \
   getattr(StringIO, '__enter__', False):
    def closing(arg):
        return arg
else:
    from contextlib import closing

try:
    _range = xrange
except NameError:
    _range = range

try:
    _unicode = unicode
except NameError:
    _unicode = str

nt_and_no_colorama = False
if os.name == 'nt':
    try:
        import colorama  # NOQA
    except ImportError:
        nt_and_no_colorama = True

# Regex definitions
# List of control characters
CTRLCHR = [r'\r', r'\n', r'\x1b\[A']  # Need to escape [ for regex
# Regular expressions compilation
RE_rate = re.compile(r'(\d+\.\d+)it/s')
RE_ctrlchr = re.compile("(%s)" % '|'.join(CTRLCHR))  # Match control chars
RE_ctrlchr_excl = re.compile('|'.join(CTRLCHR))  # Match and exclude ctrl chars
RE_pos = re.compile(
    r'((\x1b\[A|\r|\n)+((pos\d+) bar:\s+\d+%|\s{3,6})?)')  # NOQA


class DiscreteTimer(object):
    """Virtual discrete time manager, to precisely control time for tests"""

    def __init__(self):
        self.t = 0.0

    def sleep(self, t):
        """Sleep = increment the time counter (almost no CPU used)"""
        self.t += t

    def time(self):
        """Get the current time"""
        return self.t


def cpu_timify(t, timer=None):
    """Force tqdm to use the specified timer instead of system-wide time()"""
    if timer is None:
        timer = DiscreteTimer()
    t._time = timer.time
    t._sleep = timer.sleep
    t.start_t = t.last_print_t = t._time()
    return timer


def pretest():
    # setcheckinterval is deprecated
    getattr(sys, 'setswitchinterval', getattr(sys, 'setcheckinterval'))(100)

    if getattr(tqdm, "_instances", False):
        n = len(tqdm._instances)
        if n:
            tqdm._instances.clear()
            raise EnvironmentError(
                "{0} `tqdm` instances still in existence PRE-test".format(n))


def posttest():
    if getattr(tqdm, "_instances", False):
        n = len(tqdm._instances)
        if n:
            tqdm._instances.clear()
            raise EnvironmentError(
                "{0} `tqdm` instances still in existence POST-test".format(n))


class UnicodeIO(IOBase):
    """Unicode version of StringIO"""

    def __init__(self, *args, **kwargs):
        super(UnicodeIO, self).__init__(*args, **kwargs)
        self.encoding = 'U8'  # io.StringIO supports unicode, but no encoding
        self.text = ''
        self.cursor = 0

    def __len__(self):
        return len(self.text)

    def seek(self, offset):
        self.cursor = offset

    def tell(self):
        return self.cursor

    def write(self, s):
        self.text = self.text[:self.cursor] + s + \
            self.text[self.cursor + len(s):]
        self.cursor += len(s)

    def read(self, n=-1):
        _cur = self.cursor
        self.cursor = len(self) if n < 0 \
            else min(_cur + n, len(self))
        return self.text[_cur:self.cursor]

    def getvalue(self):
        return self.text


def get_bar(all_bars, i):
    """Get a specific update from a whole bar traceback"""
    # Split according to any used control characters
    bars_split = RE_ctrlchr_excl.split(all_bars)
    bars_split = list(filter(None, bars_split))  # filter out empty splits
    return bars_split[i]


def progressbar_rate(bar_str):
    return float(RE_rate.search(bar_str).group(1))


def squash_ctrlchars(s):
    """Apply control characters in a string just like a terminal display"""
    # List of supported control codes
    ctrlcodes = [r'\r', r'\n', r'\x1b\[A']

    # Init variables
    curline = 0  # current line in our fake terminal
    lines = ['']  # state of our fake terminal

    # Split input string by control codes
    RE_ctrl = re.compile("(%s)" % ("|".join(ctrlcodes)), flags=re.DOTALL)
    s_split = RE_ctrl.split(s)
    s_split = filter(None, s_split)  # filter out empty splits

    # For each control character or message
    for nextctrl in s_split:
        # If it's a control character, apply it
        if nextctrl == '\r':
            # Carriage return
            # Go to the beginning of the line
            # simplified here: we just empty the string
            lines[curline] = ''
        elif nextctrl == '\n':
            # Newline
            # Go to the next line
            if curline < (len(lines) - 1):
                # If already exists, just move cursor
                curline += 1
            else:
                # Else the new line is created
                lines.append('')
                curline += 1
        elif nextctrl == '\x1b[A':
            # Move cursor up
            if curline > 0:
                curline -= 1
            else:
                raise ValueError("Cannot go up, anymore!")
        # Else, it is a message, we print it on current line
        else:
            lines[curline] += nextctrl

    return lines


def test_format_interval():
    """Test time interval format"""
    format_interval = tqdm.format_interval

    assert format_interval(60) == '01:00'
    assert format_interval(6160) == '1:42:40'
    assert format_interval(238113) == '66:08:33'


def test_format_num():
    """Test number format"""
    format_num = tqdm.format_num

    assert float(format_num(1337)) == 1337
    assert format_num(int(1e6)) == '1e+6'
    assert format_num(1239876) == '1''239''876'


def test_format_meter():
    """Test statistics and progress bar formatting"""
    try:
        unich = unichr
    except NameError:
        unich = chr

    format_meter = tqdm.format_meter

    assert format_meter(0, 1000, 13) == \
        "  0%|          | 0/1000 [00:13<?, ?it/s]"
    # If not implementing any changes to _tqdm.py, set prefix='desc'
    # or else ": : " will be in output, so assertion should change
    assert format_meter(0, 1000, 13, ncols=68, prefix='desc: ') == \
        "desc:   0%|                                | 0/1000 [00:13<?, ?it/s]"
    assert format_meter(231, 1000, 392) == \
        " 23%|" + unich(0x2588) * 2 + unich(0x258e) + \
        "       | 231/1000 [06:32<21:44,  1.70s/it]"
    assert format_meter(10000, 1000, 13) == \
        "10000it [00:13, 769.23it/s]"
    assert format_meter(231, 1000, 392, ncols=56, ascii=True) == \
        " 23%|" + '#' * 3 + '6' + \
        "            | 231/1000 [06:32<21:44,  1.70s/it]"
    assert format_meter(100000, 1000, 13, unit_scale=True, unit='iB') == \
        "100kiB [00:13, 7.69kiB/s]"
    assert format_meter(100, 1000, 12, ncols=0, rate=7.33) == \
        " 10% 100/1000 [00:12<02:02,  7.33it/s]"
    # Check that bar_format correctly adapts {bar} size to the rest
    assert format_meter(20, 100, 12, ncols=13, rate=8.1,
                        bar_format=r'{l_bar}{bar}|{n_fmt}/{total_fmt}') == \
        " 20%|" + unich(0x258f) + "|20/100"
    assert format_meter(20, 100, 12, ncols=14, rate=8.1,
                        bar_format=r'{l_bar}{bar}|{n_fmt}/{total_fmt}') == \
        " 20%|" + unich(0x258d) + " |20/100"
    # Check that bar_format can print only {bar} or just one side
    assert format_meter(20, 100, 12, ncols=2, rate=8.1,
                        bar_format=r'{bar}') == \
        unich(0x258d) + " "
    assert format_meter(20, 100, 12, ncols=7, rate=8.1,
                        bar_format=r'{l_bar}{bar}') == \
        " 20%|" + unich(0x258d) + " "
    assert format_meter(20, 100, 12, ncols=6, rate=8.1,
                        bar_format=r'{bar}|test') == \
        unich(0x258f) + "|test"


def test_ansi_escape_codes():
    """Test stripping of ANSI escape codes"""
    format_meter = tqdm.format_meter
    ansi = {'BOLD': '\033[1m',
            'RED': '\033[91m',
            'END': '\033[0m'}
    desc = '{BOLD}{RED}Colored{END} description'.format(**ansi)
    ncols = 123
    ansi_len = sum([len(code) for code in ansi.values()])
    meter = format_meter(0, 100, 0, ncols=ncols, prefix=desc)
    assert len(meter) == ncols + ansi_len


def test_si_format():
    """Test SI unit prefixes"""
    format_meter = tqdm.format_meter

    assert '9.00 ' in format_meter(1, 9, 1, unit_scale=True, unit='B')
    assert '99.0 ' in format_meter(1, 99, 1, unit_scale=True)
    assert '999 ' in format_meter(1, 999, 1, unit_scale=True)
    assert '9.99k ' in format_meter(1, 9994, 1, unit_scale=True)
    assert '10.0k ' in format_meter(1, 9999, 1, unit_scale=True)
    assert '99.5k ' in format_meter(1, 99499, 1, unit_scale=True)
    assert '100k ' in format_meter(1, 99999, 1, unit_scale=True)
    assert '1.00M ' in format_meter(1, 999999, 1, unit_scale=True)
    assert '1.00G ' in format_meter(1, 999999999, 1, unit_scale=True)
    assert '1.00T ' in format_meter(1, 999999999999, 1, unit_scale=True)
    assert '1.00P ' in format_meter(1, 999999999999999, 1, unit_scale=True)
    assert '1.00E ' in format_meter(1, 999999999999999999, 1, unit_scale=True)
    assert '1.00Z ' in format_meter(1, 999999999999999999999, 1,
                                    unit_scale=True)
    assert '1.0Y ' in format_meter(1, 999999999999999999999999, 1,
                                   unit_scale=True)
    assert '10.0Y ' in format_meter(1, 9999999999999999999999999, 1,
                                    unit_scale=True)
    assert '100.0Y ' in format_meter(1, 99999999999999999999999999, 1,
                                     unit_scale=True)
    assert '1000.0Y ' in format_meter(1, 999999999999999999999999999, 1,
                                      unit_scale=True)


@with_setup(pretest, posttest)
def test_all_defaults():
    """Test default kwargs"""
    with closing(UnicodeIO()) as our_file:
        with tqdm(range(10), file=our_file) as progressbar:
            assert len(progressbar) == 10
            for _ in progressbar:
                pass
    # restore stdout/stderr output for `nosetest` interface
    # try:
    #     sys.stderr.write('\x1b[A')
    # except:
    #     pass
    sys.stderr.write('\rTest default kwargs ... ')


@with_setup(pretest, posttest)
def test_iterate_over_csv_rows():
    """Test csv iterator"""
    # Create a test csv pseudo file
    with closing(StringIO()) as test_csv_file:
        writer = csv.writer(test_csv_file)
        for _ in _range(3):
            writer.writerow(['test'] * 3)
        test_csv_file.seek(0)

        # Test that nothing fails if we iterate over rows
        reader = csv.DictReader(test_csv_file,
                                fieldnames=('row1', 'row2', 'row3'))
        with closing(StringIO()) as our_file:
            for _ in tqdm(reader, file=our_file):
                pass


@with_setup(pretest, posttest)
def test_file_output():
    """Test output to arbitrary file-like objects"""
    with closing(StringIO()) as our_file:
        for i in tqdm(_range(3), file=our_file):
            if i == 1:
                our_file.seek(0)
                assert '0/3' in our_file.read()


@with_setup(pretest, posttest)
def test_leave_option():
    """Test `leave=True` always prints info about the last iteration"""
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(3), file=our_file, leave=True):
            pass
        our_file.seek(0)
        assert '| 3/3 ' in our_file.read()
        our_file.seek(0)
        assert '\n' == our_file.read()[-1]  # not '\r'

    with closing(StringIO()) as our_file2:
        for _ in tqdm(_range(3), file=our_file2, leave=False):
            pass
        our_file2.seek(0)
        assert '| 3/3 ' not in our_file2.read()


@with_setup(pretest, posttest)
def test_trange():
    """Test trange"""
    with closing(StringIO()) as our_file:
        for _ in trange(3, file=our_file, leave=True):
            pass
        our_file.seek(0)
        assert '| 3/3 ' in our_file.read()

    with closing(StringIO()) as our_file2:
        for _ in trange(3, file=our_file2, leave=False):
            pass
        our_file2.seek(0)
        assert '| 3/3 ' not in our_file2.read()


@with_setup(pretest, posttest)
def test_min_interval():
    """Test mininterval"""
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(3), file=our_file, mininterval=1e-10):
            pass
        our_file.seek(0)
        assert "  0%|          | 0/3 [00:00<" in our_file.read()


@with_setup(pretest, posttest)
def test_max_interval():
    """Test maxinterval"""
    total = 100
    bigstep = 10
    smallstep = 5

    # Test without maxinterval
    timer = DiscreteTimer()
    with closing(StringIO()) as our_file:
        with closing(StringIO()) as our_file2:
            # with maxinterval but higher than loop sleep time
            t = tqdm(total=total, file=our_file, miniters=None, mininterval=0,
                     smoothing=1, maxinterval=1e-2)
            cpu_timify(t, timer)

            # without maxinterval
            t2 = tqdm(total=total, file=our_file2, miniters=None, mininterval=0,
                      smoothing=1, maxinterval=None)
            cpu_timify(t2, timer)

            assert t.dynamic_miniters
            assert t2.dynamic_miniters

            # Increase 10 iterations at once
            t.update(bigstep)
            t2.update(bigstep)
            # The next iterations should not trigger maxinterval (step 10)
            for _ in _range(4):
                t.update(smallstep)
                t2.update(smallstep)
                timer.sleep(1e-5)
            t.close()  # because PyPy doesn't gc immediately
            t2.close()  # as above

            our_file2.seek(0)
            assert "25%" not in our_file2.read()
        our_file.seek(0)
        assert "25%" not in our_file.read()

    # Test with maxinterval effect
    timer = DiscreteTimer()
    with closing(StringIO()) as our_file:
        with tqdm(total=total, file=our_file, miniters=None, mininterval=0,
                  smoothing=1, maxinterval=1e-4) as t:
            cpu_timify(t, timer)

            # Increase 10 iterations at once
            t.update(bigstep)
            # The next iterations should trigger maxinterval (step 5)
            for _ in _range(4):
                t.update(smallstep)
                timer.sleep(1e-2)

            our_file.seek(0)
            assert "25%" in our_file.read()

    # Test iteration based tqdm with maxinterval effect
    timer = DiscreteTimer()
    with closing(StringIO()) as our_file:
        with tqdm(_range(total), file=our_file, miniters=None,
                  mininterval=1e-5, smoothing=1, maxinterval=1e-4) as t2:
            cpu_timify(t2, timer)

            for i in t2:
                if i >= (bigstep - 1) and \
                   ((i - (bigstep - 1)) % smallstep) == 0:
                    timer.sleep(1e-2)
                if i >= 3 * bigstep:
                    break

        our_file.seek(0)
        assert "15%" in our_file.read()

    # Test different behavior with and without mininterval
    timer = DiscreteTimer()
    total = 1000
    mininterval = 0.1
    maxinterval = 10
    with closing(StringIO()) as our_file:
        with tqdm(total=total, file=our_file, miniters=None, smoothing=1,
                  mininterval=mininterval, maxinterval=maxinterval) as tm1:
            with tqdm(total=total, file=our_file, miniters=None, smoothing=1,
                      mininterval=0, maxinterval=maxinterval) as tm2:

                cpu_timify(tm1, timer)
                cpu_timify(tm2, timer)

                # Fast iterations, check if dynamic_miniters triggers
                timer.sleep(mininterval)  # to force update for t1
                tm1.update(total / 2)
                tm2.update(total / 2)
                assert int(tm1.miniters) == tm2.miniters == total / 2

                # Slow iterations, check different miniters if mininterval
                timer.sleep(maxinterval * 2)
                tm1.update(total / 2)
                tm2.update(total / 2)
                res = [tm1.miniters, tm2.miniters]
                assert res == [(total / 2) * mininterval / (maxinterval * 2),
                               (total / 2) * maxinterval / (maxinterval * 2)]

    # Same with iterable based tqdm
    timer1 = DiscreteTimer()  # need 2 timers for each bar because zip not work
    timer2 = DiscreteTimer()
    total = 100
    mininterval = 0.1
    maxinterval = 10
    with closing(StringIO()) as our_file:
        t1 = tqdm(_range(total), file=our_file, miniters=None, smoothing=1,
                  mininterval=mininterval, maxinterval=maxinterval)
        t2 = tqdm(_range(total), file=our_file, miniters=None, smoothing=1,
                  mininterval=0, maxinterval=maxinterval)

        cpu_timify(t1, timer1)
        cpu_timify(t2, timer2)

        for i in t1:
            if i == ((total / 2) - 2):
                timer1.sleep(mininterval)
            if i == (total - 1):
                timer1.sleep(maxinterval * 2)

        for i in t2:
            if i == ((total / 2) - 2):
                timer2.sleep(mininterval)
            if i == (total - 1):
                timer2.sleep(maxinterval * 2)

        assert t1.miniters == 0.255
        assert t2.miniters == 0.5

        t1.close()
        t2.close()


@with_setup(pretest, posttest)
def test_min_iters():
    """Test miniters"""
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(3), file=our_file, leave=True, miniters=4):
            our_file.write('blank\n')
        our_file.seek(0)
        assert '\nblank\nblank\n' in our_file.read()

    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(3), file=our_file, leave=True, miniters=1):
            our_file.write('blank\n')
        our_file.seek(0)
        # assume automatic mininterval = 0 means intermediate output
        assert '| 3/3 ' in our_file.read()


@with_setup(pretest, posttest)
def test_dynamic_min_iters():
    """Test purely dynamic miniters (and manual updates and __del__)"""
    with closing(StringIO()) as our_file:
        total = 10
        t = tqdm(total=total, file=our_file, miniters=None, mininterval=0,
                 smoothing=1)

        t.update()
        # Increase 3 iterations
        t.update(3)
        # The next two iterations should be skipped because of dynamic_miniters
        t.update()
        t.update()
        # The third iteration should be displayed
        t.update()

        our_file.seek(0)
        out = our_file.read()
        assert t.dynamic_miniters
        t.__del__()  # simulate immediate del gc

    assert '  0%|          | 0/10 [00:00<' in out
    assert '40%' in out
    assert '50%' not in out
    assert '60%' not in out
    assert '70%' in out

    # Check with smoothing=0, miniters should be set to max update seen so far
    with closing(StringIO()) as our_file:
        total = 10
        t = tqdm(total=total, file=our_file, miniters=None, mininterval=0,
                 smoothing=0)

        t.update()
        t.update(2)
        t.update(5)  # this should be stored as miniters
        t.update(1)

        our_file.seek(0)
        out = our_file.read()
        assert all(i in out for i in ("0/10", "1/10", "3/10"))
        assert "2/10" not in out
        assert t.dynamic_miniters and not t.smoothing
        assert t.miniters == 5
        t.close()

    # Check iterable based tqdm
    with closing(StringIO()) as our_file:
        t = tqdm(_range(10), file=our_file, miniters=None, mininterval=None,
                 smoothing=0.5)
        for _ in t:
            pass
        assert t.dynamic_miniters

    # No smoothing
    with closing(StringIO()) as our_file:
        t = tqdm(_range(10), file=our_file, miniters=None, mininterval=None,
                 smoothing=0)
        for _ in t:
            pass
        assert t.dynamic_miniters

    # No dynamic_miniters (miniters is fixed manually)
    with closing(StringIO()) as our_file:
        t = tqdm(_range(10), file=our_file, miniters=1, mininterval=None)
        for _ in t:
            pass
        assert not t.dynamic_miniters


@with_setup(pretest, posttest)
def test_big_min_interval():
    """Test large mininterval"""
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(2), file=our_file, mininterval=1E10):
            pass
        our_file.seek(0)
        assert '50%' not in our_file.read()

    with closing(StringIO()) as our_file:
        with tqdm(_range(2), file=our_file, mininterval=1E10) as t:
            t.update()
            t.update()
            our_file.seek(0)
            assert '50%' not in our_file.read()


@with_setup(pretest, posttest)
def test_smoothed_dynamic_min_iters():
    """Test smoothed dynamic miniters"""
    timer = DiscreteTimer()

    with closing(StringIO()) as our_file:
        with tqdm(total=100, file=our_file, miniters=None, mininterval=0,
                  smoothing=0.5, maxinterval=0) as t:
            cpu_timify(t, timer)

            # Increase 10 iterations at once
            t.update(10)
            # The next iterations should be partially skipped
            for _ in _range(2):
                t.update(4)
            for _ in _range(20):
                t.update()

            our_file.seek(0)
            out = our_file.read()
            assert t.dynamic_miniters
    assert '  0%|          | 0/100 [00:00<' in out
    assert '10%' in out
    assert '14%' not in out
    assert '18%' in out
    assert '20%' not in out
    assert '25%' in out
    assert '30%' not in out
    assert '32%' in out


@with_setup(pretest, posttest)
def test_smoothed_dynamic_min_iters_with_min_interval():
    """Test smoothed dynamic miniters with mininterval"""
    timer = DiscreteTimer()

    # In this test, `miniters` should gradually decline
    total = 100

    with closing(StringIO()) as our_file:
        # Test manual updating tqdm
        with tqdm(total=total, file=our_file, miniters=None, mininterval=1e-3,
                  smoothing=1, maxinterval=0) as t:
            cpu_timify(t, timer)

            t.update(10)
            timer.sleep(1e-2)
            for _ in _range(4):
                t.update()
                timer.sleep(1e-2)
            our_file.seek(0)
            out = our_file.read()
            assert t.dynamic_miniters

    with closing(StringIO()) as our_file:
        # Test iteration-based tqdm
        with tqdm(_range(total), file=our_file, miniters=None,
                  mininterval=0.01, smoothing=1, maxinterval=0) as t2:
            cpu_timify(t2, timer)

            for i in t2:
                if i >= 10:
                    timer.sleep(0.1)
                if i >= 14:
                    break
            our_file.seek(0)
            out2 = our_file.read()

    assert t.dynamic_miniters
    assert '  0%|          | 0/100 [00:00<' in out
    assert '11%' in out and '11%' in out2
    # assert '12%' not in out and '12%' in out2
    assert '13%' in out and '13%' in out2
    assert '14%' in out and '14%' in out2


@with_setup(pretest, posttest)
def test_disable():
    """Test disable"""
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(3), file=our_file, disable=True):
            pass
        our_file.seek(0)
        assert our_file.read() == ''

    with closing(StringIO()) as our_file:
        progressbar = tqdm(total=3, file=our_file, miniters=1, disable=True)
        progressbar.update(3)
        progressbar.close()
        our_file.seek(0)
        assert our_file.read() == ''


@with_setup(pretest, posttest)
def test_unit():
    """Test SI unit prefix"""
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(3), file=our_file, miniters=1, unit="bytes"):
            pass
        our_file.seek(0)
        assert 'bytes/s' in our_file.read()


@with_setup(pretest, posttest)
def test_ascii():
    """Test ascii/unicode bar"""
    # Test ascii autodetection
    with closing(StringIO()) as our_file:
        with tqdm(total=10, file=our_file, ascii=None) as t:
            assert t.ascii  # TODO: this may fail in the future

    # Test ascii bar
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(3), total=15, file=our_file, miniters=1,
                      mininterval=0, ascii=True):
            pass
        our_file.seek(0)
        res = our_file.read().strip("\r").split("\r")
    assert '7%|6' in res[1]
    assert '13%|#3' in res[2]
    assert '20%|##' in res[3]

    # Test unicode bar
    with closing(UnicodeIO()) as our_file:
        with tqdm(total=15, file=our_file, ascii=False, mininterval=0) as t:
            for _ in _range(3):
                t.update()
        our_file.seek(0)
        res = our_file.read().strip("\r").split("\r")
    assert "7%|\u258b" in res[1]
    assert "13%|\u2588\u258e" in res[2]
    assert "20%|\u2588\u2588" in res[3]


@with_setup(pretest, posttest)
def test_update():
    """Test manual creation and updates"""
    res = None
    with closing(StringIO()) as our_file:
        with tqdm(total=2, file=our_file, miniters=1, mininterval=0) \
                as progressbar:
            assert len(progressbar) == 2
            progressbar.update(2)
            our_file.seek(0)
            assert '| 2/2' in our_file.read()
            progressbar.desc = 'dynamically notify of 4 increments in total'
            progressbar.total = 4
            try:
                progressbar.update(-10)
            except ValueError as e:
                if str(e) != "n (-10) cannot be negative":
                    raise
                progressbar.update()  # should default to +1
            else:
                raise ValueError("Should not support negative updates")
            our_file.seek(0)
            res = our_file.read()
    assert '| 3/4 ' in res
    assert 'dynamically notify of 4 increments in total' in res


@with_setup(pretest, posttest)
def test_close():
    """Test manual creation and closure and n_instances"""

    # With `leave` option
    with closing(StringIO()) as our_file:
        progressbar = tqdm(total=3, file=our_file, miniters=10)
        progressbar.update(3)
        assert '| 3/3 ' not in our_file.getvalue()  # Should be blank
        assert len(tqdm._instances) == 1
        progressbar.close()
        assert len(tqdm._instances) == 0
        assert '| 3/3 ' in our_file.getvalue()

    # Without `leave` option
    with closing(StringIO()) as our_file:
        progressbar = tqdm(total=3, file=our_file, miniters=10, leave=False)
        progressbar.update(3)
        progressbar.close()
        assert '| 3/3 ' not in our_file.getvalue()  # Should be blank

    # With all updates
    with closing(StringIO()) as our_file:
        assert len(tqdm._instances) == 0
        with tqdm(total=3, file=our_file, miniters=0, mininterval=0,
                  leave=True) as progressbar:
            assert len(tqdm._instances) == 1
            progressbar.update(3)
            res = our_file.getvalue()
            assert '| 3/3 ' in res  # Should be blank
        # close() called
        assert len(tqdm._instances) == 0
        our_file.seek(0)

        exres = res + '\n'
        if exres != our_file.read():
            our_file.seek(0)
            raise AssertionError(
                "\nExpected:\n{0}\nGot:{1}\n".format(exres, our_file.read()))

    # Closing after the output stream has closed
    with closing(StringIO()) as our_file:
        t = tqdm(total=2, file=our_file)
        t.update()
        t.update()
    t.close()


@with_setup(pretest, posttest)
def test_smoothing():
    """Test exponential weighted average smoothing"""
    timer = DiscreteTimer()

    # -- Test disabling smoothing
    with closing(StringIO()) as our_file:
        with tqdm(_range(3), file=our_file, smoothing=None, leave=True) as t:
            cpu_timify(t, timer)

            for _ in t:
                pass
        our_file.seek(0)
        assert '| 3/3 ' in our_file.read()

    # -- Test smoothing
    # Compile the regex to find the rate
    # 1st case: no smoothing (only use average)
    with closing(StringIO()) as our_file2:
        with closing(StringIO()) as our_file:
            t = tqdm(_range(3), file=our_file2, smoothing=None, leave=True,
                     miniters=1, mininterval=0)
            cpu_timify(t, timer)

            with tqdm(_range(3), file=our_file, smoothing=None, leave=True,
                      miniters=1, mininterval=0) as t2:
                cpu_timify(t2, timer)

                for i in t2:
                    # Sleep more for first iteration and
                    # see how quickly rate is updated
                    if i == 0:
                        timer.sleep(0.01)
                    else:
                        # Need to sleep in all iterations
                        # to calculate smoothed rate
                        # (else delta_t is 0!)
                        timer.sleep(0.001)
                    t.update()
            n_old = len(tqdm._instances)
            t.close()
            assert len(tqdm._instances) == n_old - 1
            # Get result for iter-based bar
            a = progressbar_rate(get_bar(our_file.getvalue(), 3))
        # Get result for manually updated bar
        a2 = progressbar_rate(get_bar(our_file2.getvalue(), 3))

    # 2nd case: use max smoothing (= instant rate)
    with closing(StringIO()) as our_file2:
        with closing(StringIO()) as our_file:
            t = tqdm(_range(3), file=our_file2, smoothing=1, leave=True,
                     miniters=1, mininterval=0)
            cpu_timify(t, timer)

            with tqdm(_range(3), file=our_file, smoothing=1, leave=True,
                      miniters=1, mininterval=0) as t2:
                cpu_timify(t2, timer)

                for i in t2:
                    if i == 0:
                        timer.sleep(0.01)
                    else:
                        timer.sleep(0.001)
                    t.update()
            t.close()
            # Get result for iter-based bar
            b = progressbar_rate(get_bar(our_file.getvalue(), 3))
        # Get result for manually updated bar
        b2 = progressbar_rate(get_bar(our_file2.getvalue(), 3))

    # 3rd case: use medium smoothing
    with closing(StringIO()) as our_file2:
        with closing(StringIO()) as our_file:
            t = tqdm(_range(3), file=our_file2, smoothing=0.5, leave=True,
                     miniters=1, mininterval=0)
            cpu_timify(t, timer)

            t2 = tqdm(_range(3), file=our_file, smoothing=0.5, leave=True,
                      miniters=1, mininterval=0)
            cpu_timify(t2, timer)

            for i in t2:
                if i == 0:
                    timer.sleep(0.01)
                else:
                    timer.sleep(0.001)
                t.update()
            t2.close()
            t.close()
            # Get result for iter-based bar
            c = progressbar_rate(get_bar(our_file.getvalue(), 3))
        # Get result for manually updated bar
        c2 = progressbar_rate(get_bar(our_file2.getvalue(), 3))

    # Check that medium smoothing's rate is between no and max smoothing rates
    assert a <= c <= b
    assert a2 <= c2 <= b2


@with_setup(pretest, posttest)
def test_deprecated_nested():
    """Test nested progress bars"""
    if nt_and_no_colorama:
        raise SkipTest
    # TODO: test degradation on windows without colorama?

    # Artificially test nested loop printing
    # Without leave
    our_file = StringIO()
    try:
        tqdm(total=2, file=our_file, nested=True)
    except TqdmDeprecationWarning:
        if """`nested` is deprecated and automated.\
 Use position instead for manual control.""" not in our_file.getvalue():
            raise
    else:
        raise DeprecationError("Should not allow nested kwarg")


@with_setup(pretest, posttest)
def test_bar_format():
    """Test custom bar formatting"""
    with closing(StringIO()) as our_file:
        bar_format = r'{l_bar}{bar}|{n_fmt}/{total_fmt}-{n}/{total}{percentage}{rate}{rate_fmt}{elapsed}{remaining}'  # NOQA
        for _ in trange(2, file=our_file, leave=True, bar_format=bar_format):
            pass
        out = our_file.getvalue()
    assert "\r  0%|          |0/2-0/20.0None?it/s00:00?\r" in out

    # Test unicode string auto conversion
    with closing(StringIO()) as our_file:
        bar_format = r'hello world'
        with tqdm(ascii=False, bar_format=bar_format, file=our_file) as t:
            assert isinstance(t.bar_format, _unicode)


@with_setup(pretest, posttest)
def test_unpause():
    """Test unpause"""
    timer = DiscreteTimer()
    with closing(StringIO()) as our_file:
        t = trange(10, file=our_file, leave=True, mininterval=0)
        cpu_timify(t, timer)
        timer.sleep(0.01)
        t.update()
        timer.sleep(0.01)
        t.update()
        timer.sleep(0.1)  # longer wait time
        t.unpause()
        timer.sleep(0.01)
        t.update()
        timer.sleep(0.01)
        t.update()
        t.close()
        r_before = progressbar_rate(get_bar(our_file.getvalue(), 2))
        r_after = progressbar_rate(get_bar(our_file.getvalue(), 3))
    assert r_before == r_after


@with_setup(pretest, posttest)
def test_position():
    """Test positioned progress bars"""
    if nt_and_no_colorama:
        raise SkipTest

    # Artificially test nested loop printing
    # Without leave
    our_file = StringIO()
    kwargs = dict(file=our_file, miniters=1, mininterval=0, maxinterval=0)
    t = tqdm(total=2, desc='pos2 bar', leave=False, position=2, **kwargs)
    t.update()
    t.close()
    our_file.seek(0)
    out = our_file.read()
    res = [m[0] for m in RE_pos.findall(out)]
    exres = ['\n\n\rpos2 bar:   0%',
             '\x1b[A\x1b[A\n\n\rpos2 bar:  50%',
             '\x1b[A\x1b[A\n\n\r      ',
             '\x1b[A\x1b[A']
    if res != exres:
        raise AssertionError("\nExpected:\n{0}\nGot:\n{1}\nRaw:\n{2}\n".format(
            str(exres), str(res), str([out])))

    # Test iteration-based tqdm positioning
    our_file = StringIO()
    kwargs["file"] = our_file
    for _ in trange(2, desc='pos0 bar', position=0, **kwargs):
        for _ in trange(2, desc='pos1 bar', position=1, **kwargs):
            for _ in trange(2, desc='pos2 bar', position=2, **kwargs):
                pass
    our_file.seek(0)
    out = our_file.read()
    res = [m[0] for m in RE_pos.findall(out)]
    exres = ['\rpos0 bar:   0%',
             '\n\rpos1 bar:   0%',
             '\x1b[A\n\n\rpos2 bar:   0%',
             '\x1b[A\x1b[A\n\n\rpos2 bar:  50%',
             '\x1b[A\x1b[A\n\n\rpos2 bar: 100%',
             '\x1b[A\x1b[A\n\n\x1b[A\x1b[A\n\rpos1 bar:  50%',
             '\x1b[A\n\n\rpos2 bar:   0%',
             '\x1b[A\x1b[A\n\n\rpos2 bar:  50%',
             '\x1b[A\x1b[A\n\n\rpos2 bar: 100%',
             '\x1b[A\x1b[A\n\n\x1b[A\x1b[A\n\rpos1 bar: 100%',
             '\x1b[A\n\x1b[A\rpos0 bar:  50%',
             '\n\rpos1 bar:   0%',
             '\x1b[A\n\n\rpos2 bar:   0%',
             '\x1b[A\x1b[A\n\n\rpos2 bar:  50%',
             '\x1b[A\x1b[A\n\n\rpos2 bar: 100%',
             '\x1b[A\x1b[A\n\n\x1b[A\x1b[A\n\rpos1 bar:  50%',
             '\x1b[A\n\n\rpos2 bar:   0%',
             '\x1b[A\x1b[A\n\n\rpos2 bar:  50%',
             '\x1b[A\x1b[A\n\n\rpos2 bar: 100%',
             '\x1b[A\x1b[A\n\n\x1b[A\x1b[A\n\rpos1 bar: 100%',
             '\x1b[A\n\x1b[A\rpos0 bar: 100%',
             '\n']
    if res != exres:
        raise AssertionError("\nExpected:\n{0}\nGot:\n{1}\nRaw:\n{2}\n".format(
            str(exres), str(res), str([out])))

    # Test manual tqdm positioning
    our_file = StringIO()
    kwargs["file"] = our_file
    kwargs["total"] = 2
    t1 = tqdm(desc='pos0 bar', position=0, **kwargs)
    t2 = tqdm(desc='pos1 bar', position=1, **kwargs)
    t3 = tqdm(desc='pos2 bar', position=2, **kwargs)
    for _ in _range(2):
        t1.update()
        t3.update()
        t2.update()
    our_file.seek(0)
    out = our_file.read()
    res = [m[0] for m in RE_pos.findall(out)]
    exres = ['\rpos0 bar:   0%',
             '\n\rpos1 bar:   0%',
             '\x1b[A\n\n\rpos2 bar:   0%',
             '\x1b[A\x1b[A\rpos0 bar:  50%',
             '\n\n\rpos2 bar:  50%',
             '\x1b[A\x1b[A\n\rpos1 bar:  50%',
             '\x1b[A\rpos0 bar: 100%',
             '\n\n\rpos2 bar: 100%',
             '\x1b[A\x1b[A\n\rpos1 bar: 100%',
             '\x1b[A']
    if res != exres:
        raise AssertionError("\nExpected:\n{0}\nGot:\n{1}\nRaw:\n{2}\n".format(
            str(exres), str(res), str([out])))
    t1.close()
    t2.close()
    t3.close()

    # Test auto repositionning of bars when a bar is prematurely closed
    # tqdm._instances.clear()  # reset number of instances
    with closing(StringIO()) as our_file:
        t1 = tqdm(total=10, file=our_file, desc='pos0 bar', mininterval=0)
        t2 = tqdm(total=10, file=our_file, desc='pos1 bar', mininterval=0)
        t3 = tqdm(total=10, file=our_file, desc='pos2 bar', mininterval=0)
        res = [m[0] for m in RE_pos.findall(our_file.getvalue())]
        exres = ['\rpos0 bar:   0%',
                 '\n\rpos1 bar:   0%',
                 '\x1b[A\n\n\rpos2 bar:   0%',
                 '\x1b[A\x1b[A']
        if res != exres:
            raise AssertionError(
                "\nExpected:\n{0}\nGot:\n{1}\n".format(str(exres), str(res)))

        t2.close()
        t4 = tqdm(total=10, file=our_file, desc='pos3 bar', mininterval=0)
        t1.update(1)
        t3.update(1)
        t4.update(1)
        res = [m[0] for m in RE_pos.findall(our_file.getvalue())]
        exres = ['\rpos0 bar:   0%',
                 '\n\rpos1 bar:   0%',
                 '\x1b[A\n\n\rpos2 bar:   0%',
                 '\x1b[A\x1b[A\n\x1b[A\n\n\rpos3 bar:   0%',
                 '\x1b[A\x1b[A\rpos0 bar:  10%',
                 '\n\rpos2 bar:  10%',
                 '\x1b[A\n\n\rpos3 bar:  10%',
                 '\x1b[A\x1b[A']
        if res != exres:
            raise AssertionError(
                "\nExpected:\n{0}\nGot:\n{1}\n".format(str(exres), str(res)))
        t4.close()
        t3.close()
        t1.close()


@with_setup(pretest, posttest)
def test_set_description():
    """Test set description"""
    with closing(StringIO()) as our_file:
        with tqdm(desc='Hello', file=our_file) as t:
            assert t.desc == 'Hello'
            t.set_description_str('World')
            assert t.desc == 'World'
            t.set_description()
            assert t.desc == ''
            t.set_description('Bye')
            assert t.desc == 'Bye: '
        assert "World" in our_file.getvalue()

    # without refresh
    with closing(StringIO()) as our_file:
        with tqdm(desc='Hello', file=our_file) as t:
            assert t.desc == 'Hello'
            t.set_description_str('World', False)
            assert t.desc == 'World'
            t.set_description(None, False)
            assert t.desc == ''
        assert "World" not in our_file.getvalue()


@with_setup(pretest, posttest)
def test_deprecated_gui():
    """Test internal GUI properties"""
    # Check: StatusPrinter iff gui is disabled
    with closing(StringIO()) as our_file:
        t = tqdm(total=2, gui=True, file=our_file, miniters=1, mininterval=0)
        assert not hasattr(t, "sp")
        try:
            t.update(1)
        except TqdmDeprecationWarning as e:
            if 'Please use `tqdm_gui(...)` instead of `tqdm(..., gui=True)`' \
                    not in our_file.getvalue():
                raise e
        else:
            raise DeprecationError('Should not allow manual gui=True without'
                                   ' overriding __iter__() and update()')
        finally:
            t._instances.clear()
            # t.close()
            # len(tqdm._instances) += 1  # undo the close() decrement

        t = tqdm(_range(3), gui=True, file=our_file, miniters=1, mininterval=0)
        try:
            for _ in t:
                pass
        except TqdmDeprecationWarning as e:
            if 'Please use `tqdm_gui(...)` instead of `tqdm(..., gui=True)`' \
                    not in our_file.getvalue():
                raise e
        else:
            raise DeprecationError('Should not allow manual gui=True without'
                                   ' overriding __iter__() and update()')
        finally:
            t._instances.clear()
            # t.close()
            # len(tqdm._instances) += 1  # undo the close() decrement

        with tqdm(total=1, gui=False, file=our_file) as t:
            assert hasattr(t, "sp")


@with_setup(pretest, posttest)
def test_cmp():
    """Test comparison functions"""
    with closing(StringIO()) as our_file:
        t0 = tqdm(total=10, file=our_file)
        t1 = tqdm(total=10, file=our_file)
        t2 = tqdm(total=10, file=our_file)

        assert t0 < t1
        assert t2 >= t0
        assert t0 <= t2

        t3 = tqdm(total=10, file=our_file)
        t4 = tqdm(total=10, file=our_file)
        t5 = tqdm(total=10, file=our_file)
        t5.close()
        t6 = tqdm(total=10, file=our_file)

        assert t3 != t4
        assert t3 > t2
        assert t5 == t6
        t6.close()
        t4.close()
        t3.close()
        t2.close()
        t1.close()
        t0.close()


@with_setup(pretest, posttest)
def test_repr():
    """Test representation"""
    with closing(StringIO()) as our_file:
        with tqdm(total=10, ascii=True, file=our_file) as t:
            assert str(t) == '  0%|          | 0/10 [00:00<?, ?it/s]'


@with_setup(pretest, posttest)
def test_clear():
    """Test clearing bar display"""
    with closing(StringIO()) as our_file:
        t1 = tqdm(total=10, file=our_file, desc='pos0 bar',
                  bar_format='{l_bar}')
        t2 = trange(10, file=our_file, desc='pos1 bar', bar_format='{l_bar}')
        before = squash_ctrlchars(our_file.getvalue())
        t2.clear()
        t1.clear()
        after = squash_ctrlchars(our_file.getvalue())
        t1.close()
        t2.close()
        assert before == ['pos0 bar:   0%|', 'pos1 bar:   0%|']
        assert after == ['', '']


@with_setup(pretest, posttest)
def test_clear_disabled():
    """Test clearing bar display"""
    with closing(StringIO()) as our_file:
        with tqdm(total=10, file=our_file, desc='pos0 bar', disable=True,
                  bar_format='{l_bar}') as t:
            t.clear()
        assert our_file.getvalue() == ''


@with_setup(pretest, posttest)
def test_refresh():
    """Test refresh bar display"""
    with closing(StringIO()) as our_file:
        t1 = tqdm(total=10, file=our_file, desc='pos0 bar',
                  bar_format='{l_bar}', mininterval=999, miniters=999)
        t2 = tqdm(total=10, file=our_file, desc='pos1 bar',
                  bar_format='{l_bar}', mininterval=999, miniters=999)
        t1.update()
        t2.update()
        before = squash_ctrlchars(our_file.getvalue())
        t1.refresh()
        t2.refresh()
        after = squash_ctrlchars(our_file.getvalue())
        t1.close()
        t2.close()

        # Check that refreshing indeed forced the display to use realtime state
        assert before == [u'pos0 bar:   0%|', u'pos1 bar:   0%|']
        assert after == [u'pos0 bar:  10%|', u'pos1 bar:  10%|']


@with_setup(pretest, posttest)
def test_disabled_refresh():
    """Test refresh bar display"""
    with closing(StringIO()) as our_file:
        with tqdm(total=10, file=our_file, desc='pos0 bar', disable=True,
                  bar_format='{l_bar}', mininterval=999, miniters=999) as t:
            t.update()
            t.refresh()

        assert our_file.getvalue() == ''


@with_setup(pretest, posttest)
def test_write():
    """Test write messages"""
    s = "Hello world"
    with closing(StringIO()) as our_file:
        # Change format to keep only left part w/o bar and it/s rate
        t1 = tqdm(total=10, file=our_file, desc='pos0 bar',
                  bar_format='{l_bar}', mininterval=0, miniters=1)
        t2 = trange(10, file=our_file, desc='pos1 bar', bar_format='{l_bar}',
                    mininterval=0, miniters=1)
        t3 = tqdm(total=10, file=our_file, desc='pos2 bar',
                  bar_format='{l_bar}', mininterval=0, miniters=1)
        t1.update()
        t2.update()
        t3.update()
        before = our_file.getvalue()

        # Write msg and see if bars are correctly redrawn below the msg
        t1.write(s, file=our_file)  # call as an instance method
        tqdm.write(s, file=our_file)  # call as a class method
        after = our_file.getvalue()

        t1.close()
        t2.close()
        t3.close()

        before_squashed = squash_ctrlchars(before)
        after_squashed = squash_ctrlchars(after)

        assert after_squashed == [s, s] + before_squashed

    # Check that no bar clearing if different file
    with closing(StringIO()) as our_file_bar:
        with closing(StringIO()) as our_file_write:
            t1 = tqdm(total=10, file=our_file_bar, desc='pos0 bar',
                      bar_format='{l_bar}', mininterval=0, miniters=1)

            t1.update()
            before_bar = our_file_bar.getvalue()

            tqdm.write(s, file=our_file_write)

            after_bar = our_file_bar.getvalue()
            t1.close()

            assert before_bar == after_bar

    # Test stdout/stderr anti-mixup strategy
    # Backup stdout/stderr
    stde = sys.stderr
    stdo = sys.stdout
    # Mock stdout/stderr
    with closing(StringIO()) as our_stderr:
        with closing(StringIO()) as our_stdout:
            sys.stderr = our_stderr
            sys.stdout = our_stdout
            t1 = tqdm(total=10, file=sys.stderr, desc='pos0 bar',
                      bar_format='{l_bar}', mininterval=0, miniters=1)

            t1.update()
            before_err = sys.stderr.getvalue()
            before_out = sys.stdout.getvalue()

            tqdm.write(s, file=sys.stdout)
            after_err = sys.stderr.getvalue()
            after_out = sys.stdout.getvalue()

            t1.close()

            assert before_err == '\rpos0 bar:   0%|\rpos0 bar:  10%|'
            assert before_out == ''
            after_err_res = [m[0] for m in RE_pos.findall(after_err)]
            assert after_err_res == [u'\rpos0 bar:   0%',
                                     u'\rpos0 bar:  10%',
                                     u'\r      ',
                                     u'\r\rpos0 bar:  10%']
            assert after_out == s + '\n'
    # Restore stdout and stderr
    sys.stderr = stde
    sys.stdout = stdo


@with_setup(pretest, posttest)
def test_len():
    """Test advance len (numpy array shape)"""
    try:
        import numpy as np
    except ImportError:
        raise SkipTest
    with closing(StringIO()) as f:
        with tqdm(np.zeros((3, 4)), file=f) as t:
            assert len(t) == 3


@with_setup(pretest, posttest)
def test_autodisable_disable():
    """Test autodisable will disable on non-TTY"""
    with closing(StringIO()) as our_file:
        with tqdm(total=10, disable=None, file=our_file) as t:
            t.update(3)
        assert our_file.getvalue() == ''


@with_setup(pretest, posttest)
def test_autodisable_enable():
    """Test autodisable will not disable on TTY"""
    with closing(StringIO()) as our_file:
        setattr(our_file, "isatty", lambda: True)
        with tqdm(total=10, disable=None, file=our_file) as t:
            t.update()
        assert our_file.getvalue() != ''


@with_setup(pretest, posttest)
def test_deprecation_exception():
    def test_TqdmDeprecationWarning():
        with closing(StringIO()) as our_file:
            raise (TqdmDeprecationWarning('Test!', fp_write=getattr(
                our_file, 'write', sys.stderr.write)))

    def test_TqdmDeprecationWarning_nofpwrite():
        raise (TqdmDeprecationWarning('Test!', fp_write=None))

    assert_raises(TqdmDeprecationWarning, test_TqdmDeprecationWarning)
    assert_raises(Exception, test_TqdmDeprecationWarning_nofpwrite)


@with_setup(pretest, posttest)
def test_postfix():
    """Test postfix"""
    postfix = {'float': 0.321034, 'gen': 543, 'str': 'h', 'lst': [2]}
    postfix_order = (('w', 'w'), ('a', 0))  # no need for OrderedDict
    expected = ['float=0.321', 'gen=543', 'lst=[2]', 'str=h']
    expected_order = ['w=w', 'a=0', 'float=0.321', 'gen=543', 'lst=[2]',
                      'str=h']

    # Test postfix set at init
    with closing(StringIO()) as our_file:
        with tqdm(total=10, file=our_file, desc='pos0 bar',
                  bar_format='{r_bar}', postfix=postfix) as t1:
            t1.refresh()
            out = our_file.getvalue()

    # Test postfix set after init
    with closing(StringIO()) as our_file:
        with trange(10, file=our_file, desc='pos1 bar', bar_format='{r_bar}',
                    postfix=None) as t2:
            t2.set_postfix(**postfix)
            t2.refresh()
            out2 = our_file.getvalue()

    # Order of items in dict may change, so need a loop to check per item
    for res in expected:
        assert res in out
        assert res in out2

    # Test postfix (with ordered dict and no refresh) set after init
    with closing(StringIO()) as our_file:
        with trange(10, file=our_file, desc='pos2 bar', bar_format='{r_bar}',
                    postfix=None) as t3:
            t3.set_postfix(postfix_order, False, **postfix)
            t3.refresh()  # explicit external refresh
            out3 = our_file.getvalue()

    out3 = out3[1:-1].split(', ')[3:]
    assert out3 == expected_order

    # Test postfix (with ordered dict and refresh) set after init
    with closing(StringIO()) as our_file:
        with trange(10, file=our_file, desc='pos2 bar',
                    bar_format='{r_bar}', postfix=None) as t4:
            t4.set_postfix(postfix_order, True, **postfix)
            t4.refresh()  # double refresh
            out4 = our_file.getvalue()

    assert out4.count('\r') > out3.count('\r')
    assert out4.count(", ".join(expected_order)) == 2

    # Test setting postfix string directly
    with closing(StringIO()) as our_file:
        with trange(10, file=our_file, desc='pos2 bar', bar_format='{r_bar}',
                    postfix=None) as t5:
            t5.set_postfix_str("Hello", False)
            t5.set_postfix_str("World")
            out5 = our_file.getvalue()

    assert "Hello" not in out5
    out5 = out5[1:-1].split(', ')[3:]
    assert out5 == ["World"]


def test_postfix_direct():
    """Test directly assigning non-str objects to postfix"""
    with closing(StringIO()) as our_file:
        with tqdm(total=10, file=our_file, miniters=1, mininterval=0,
                  bar_format="{postfix[0][name]} {postfix[1]:>5.2f}",
                  postfix=[dict(name="foo"), 42]) as t:
            for i in range(10):
                if i % 2:
                    t.postfix[0]["name"] = "abcdefghij"[i]
                else:
                    t.postfix[1] = i
                t.update()
        res = our_file.getvalue()
        assert "f  6.00" in res
        assert "h  6.00" in res
        assert "h  8.00" in res
        assert "j  8.00" in res


class DummyTqdmFile(object):
    """Dummy file-like that will write to tqdm"""
    file = None

    def __init__(self, file):
        self.file = file

    def write(self, x):
        # Avoid print() second call (useless \n)
        if len(x.rstrip()) > 0:
            tqdm.write(x, file=self.file, nolock=True)


@contextmanager
def std_out_err_redirect_tqdm(tqdm_file=sys.stderr):
    orig_out_err = sys.stdout, sys.stderr
    try:
        sys.stdout = sys.stderr = DummyTqdmFile(tqdm_file)
        yield orig_out_err[0]
    # Relay exceptions
    except Exception as exc:
        raise exc
    # Always restore sys.stdout/err if necessary
    finally:
        sys.stdout, sys.stderr = orig_out_err


@with_setup(pretest, posttest)
def test_file_redirection():
    """Test redirection of output"""
    with closing(StringIO()) as our_file:
        # Redirect stdout to tqdm.write()
        with std_out_err_redirect_tqdm(tqdm_file=our_file):
            for _ in trange(3):
                print("Such fun")
        res = our_file.getvalue()
        assert res.count("Such fun\n") == 3
        assert "0/3" in res
        assert "3/3" in res


@with_setup(pretest, posttest)
def test_external_write():
    """Test external write mode"""
    with closing(StringIO()) as our_file:
        # Redirect stdout to tqdm.write()
        for _ in trange(3, file=our_file):
            with tqdm.external_write_mode(file=our_file):
                our_file.write("Such fun\n")
        res = our_file.getvalue()
        assert res.count("Such fun\n") == 3
        assert "0/3" in res
        assert "3/3" in res


@with_setup(pretest, posttest)
def test_unit_scale():
    """Test numeric `unit_scale`"""
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(100), unit_scale=9, file=our_file):
            pass
        out = our_file.getvalue()
        assert '900/900' in out


@with_setup(pretest, posttest)
def test_threading():
    """Test multiprocess/thread-realted features"""
    from multiprocessing import RLock
    try:
        mp_lock = RLock()
    except OSError:
        pass
    else:
        tqdm.set_lock(mp_lock)
    # TODO: test interleaved output #445


@with_setup(pretest, posttest)
def test_bool():
    """Test boolean cast"""
    def internal(our_file, disable):
        with tqdm(total=10, file=our_file, disable=disable) as t:
            assert t
        with tqdm(total=0, file=our_file, disable=disable) as t:
            assert not t
        with trange(10, file=our_file, disable=disable) as t:
            assert t
        with trange(0, file=our_file, disable=disable) as t:
            assert not t
        with tqdm([], file=our_file, disable=disable) as t:
            assert not t
        with tqdm([0], file=our_file, disable=disable) as t:
            assert t
        with tqdm(file=our_file, disable=disable) as t:
            try:
                print(bool(t))
            except TypeError:
                pass
            else:
                raise TypeError(
                    "Expected tqdm() with neither total nor iterable to fail")

    # test with and without disable
    with closing(StringIO()) as our_file:
        internal(our_file, False)
        internal(our_file, True)


def backendCheck(module):
    """Test tqdm-like module fallback"""
    tn = module.tqdm
    tr = module.trange

    with closing(StringIO()) as our_file:
        with tn(total=10, file=our_file) as t:
            assert len(t) == 10
        with tr(1337) as t:
            assert len(t) == 1337


@with_setup(pretest, posttest)
def test_auto():
    """Test auto fallback"""
    from tqdm import autonotebook, auto
    backendCheck(autonotebook)
    backendCheck(auto)
