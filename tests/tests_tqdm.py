import csv
import os
import re
import sys
from importlib import import_module
from io import BytesIO, IOBase

from pytest import importorskip, mark, raises, warns

from tqdm import TqdmDeprecationWarning, TqdmWarning, tqdm, trange
from tqdm.contrib import DummyTqdmFile
from tqdm.std import EMA, Bar

nt_and_no_colorama = False
if os.name == 'nt':
    try:
        import colorama  # noqa: F401, pylint: disable=unused-import
    except ImportError:
        nt_and_no_colorama = True

# Regex definitions
# List of control characters
CTRLCHR = [r'\r', r'\n', r'\x1b\[A']  # Need to escape [ for regex
# Regular expressions compilation
RE_rate = re.compile(r'[^\d](\d[.\d]+)it/s')
RE_ctrlchr = re.compile("(%s)" % '|'.join(CTRLCHR))  # Match control chars
RE_ctrlchr_excl = re.compile('|'.join(CTRLCHR))  # Match and exclude ctrl chars
RE_pos = re.compile(r'([\r\n]+((pos\d+) bar:\s+\d+%|\s{3,6})?[^\r\n]*)')


def pos_line_diff(res_list, expected_list, raise_nonempty=True):
    """
    Return differences between two bar output lists.
    To be used with `RE_pos`
    """
    res = [(r, e) for r, e in zip(res_list, expected_list)
           for pos in [len(e) - len(e.lstrip('\n'))]  # bar position
           if r != e  # simple comparison
           if not r.startswith(e)  # start matches
           or not (
               # move up at end (maybe less due to closing bars)
               any(r.endswith(end + i * '\x1b[A') for i in range(pos + 1)
                   for end in [
                       ']',  # bar
                       '  '])  # cleared
               or '100%' in r  # completed bar
               or r == '\n')  # final bar
           or r[(-1 - pos) * len('\x1b[A'):] == '\x1b[A']  # too many moves up
    if raise_nonempty and (res or len(res_list) != len(expected_list)):
        if len(res_list) < len(expected_list):
            res.extend([(None, e) for e in expected_list[len(res_list):]])
        elif len(res_list) > len(expected_list):
            res.extend([(r, None) for r in res_list[len(expected_list):]])
        raise AssertionError(
            "Got => Expected\n" + '\n'.join('%r => %r' % i for i in res))
    return res


class DiscreteTimer:
    """Virtual discrete time manager, to precisely control time for tests"""
    def __init__(self):
        self.t = 0.0

    def sleep(self, t):
        """Sleep = increment the time counter (almost no CPU used)"""
        self.t += t

    def time(self):
        return self.t


def cpu_timify(t, timer=None):
    """Force tqdm to use the specified timer instead of system-wide time()"""
    if timer is None:
        timer = DiscreteTimer()
    t._time = timer.time
    t._sleep = timer.sleep
    t.start_t = t.last_print_t = t._time()
    return timer


class UnicodeIO(IOBase):
    """Unicode version of StringIO"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.text = self.text[:self.cursor] + s + self.text[self.cursor + len(s):]
        self.cursor += len(s)

    def read(self, n=-1):
        _cur = self.cursor
        self.cursor = len(self) if n < 0 else min(_cur + n, len(self))
        return self.text[_cur:self.cursor]

    def getvalue(self):
        return self.text


def get_bar(all_bars, i=None):
    """Get a specific update from a whole bar traceback"""
    # Split according to any used control characters
    bars_split = RE_ctrlchr_excl.split(all_bars)
    bars_split = list(filter(None, bars_split))  # filter out empty splits
    return bars_split if i is None else bars_split[i]


def progressbar_rate(bar_str):
    return float(RE_rate.search(bar_str).group(1))


def squash_ctrlchars(s):
    """Apply control characters in a string just like a terminal display"""
    curline = 0
    lines = ['']  # state of fake terminal
    for nextctrl in filter(None, RE_ctrlchr.split(s)):
        # apply control chars
        if nextctrl == '\r':
            # go to line beginning (simplified here: just empty the string)
            lines[curline] = ''
        elif nextctrl == '\n':
            if curline >= len(lines) - 1:
                # wrap-around creates newline
                lines.append('')
            # move cursor down
            curline += 1
        elif nextctrl == '\x1b[A':
            # move cursor up
            if curline > 0:
                curline -= 1
            else:
                raise ValueError("Cannot go further up")
        else:
            # print message on current line
            lines[curline] += nextctrl
    return lines


def test_format_interval():
    format_interval = tqdm.format_interval

    assert format_interval(60) == '01:00'
    assert format_interval(6160) == '1:42:40'
    assert format_interval(238113) == '66:08:33'
    assert format_interval(-1) == '-00:01'
    assert format_interval(-60) == '-01:00'
    assert format_interval(-100000) == '-27:46:40'
    assert format_interval(0) == '00:00'


def test_format_num():
    format_num = tqdm.format_num

    assert float(format_num(1337)) == 1337
    assert format_num(int(1e6)) == '1e+6'
    assert format_num(1239876) == '1' '239' '876'
    assert format_num(0.00001234) == '1.23e-5'
    assert format_num(-0.1234) == '-0.123'


def test_format_meter():
    format_meter = tqdm.format_meter

    assert format_meter(0, 1000, 13) == "  0%|          | 0/1000 [00:13<?, ?it/s]"
    # If not implementing any changes to _tqdm.py, set prefix='desc'
    # or else ": : " will be in output, so assertion should change
    assert format_meter(0, 1000, 13, ncols=68, prefix='desc: ') == (
        "desc:   0%|                                | 0/1000 [00:13<?, ?it/s]")
    assert format_meter(231, 1000, 392) == (" 23%|\u2588\u2588\u258e"
                                            "       | 231/1000 [06:32<21:44,  1.70s/it]")
    assert format_meter(10000, 1000, 13) == "10000it [00:13, 769.23it/s]"
    assert format_meter(5, float("inf"), 1) == format_meter(5, None, 1)
    assert format_meter(231, 1000, 392, ncols=56, ascii=True) == " 23%|" + '#' * 3 + '6' + (
        "            | 231/1000 [06:32<21:44,  1.70s/it]")
    assert format_meter(100000, 1000, 13, unit_scale=True,
                        unit='iB') == "100kiB [00:13, 7.69kiB/s]"
    assert format_meter(100, 1000, 12, ncols=0,
                        rate=7.33) == " 10% 100/1000 [00:12<02:02,  7.33it/s]"
    # ncols is small, l_bar is too large
    # l_bar gets chopped
    # no bar
    # no r_bar
    # 10/12 stars since ncols is 10
    assert format_meter(
        0, 1000, 13, ncols=10,
        bar_format="************{bar:10}$$$$$$$$$$") == "**********"
    # n_cols allows for l_bar and some of bar
    # l_bar displays
    # bar gets chopped
    # no r_bar
    # all 12 stars and 8/10 bar parts
    assert format_meter(
        0, 1000, 13, ncols=20,
        bar_format="************{bar:10}$$$$$$$$$$") == "************        "
    # n_cols allows for l_bar, bar, and some of r_bar
    # l_bar displays
    # bar displays
    # r_bar gets chopped
    # all 12 stars and 10 bar parts, but only 8/10 dollar signs
    assert format_meter(
        0, 1000, 13, ncols=30,
        bar_format="************{bar:10}$$$$$$$$$$") == "************          $$$$$$$$"
    # trim left ANSI; escape is before trim zone
    # we only know it has ANSI codes, so we append an END code anyway
    assert format_meter(
        0, 1000, 13, ncols=10, bar_format="*****\033[22m****\033[0m***{bar:10}$$$$$$$$$$"
    ) == "*****\033[22m****\033[0m*\033[0m"
    # trim left ANSI; escape is at trim zone
    assert format_meter(
        0, 1000, 13, ncols=10,
        bar_format="*****\033[22m*****\033[0m**{bar:10}$$$$$$$$$$") == "*****\033[22m*****\033[0m"
    # trim left ANSI; escape is after trim zone
    assert format_meter(
        0, 1000, 13, ncols=10,
        bar_format="*****\033[22m******\033[0m*{bar:10}$$$$$$$$$$") == "*****\033[22m*****\033[0m"
    # Check that bar_format correctly adapts {bar} size to the rest
    assert format_meter(
        20, 100, 12, ncols=13, rate=8.1,
        bar_format=r'{l_bar}{bar}|{n_fmt}/{total_fmt}') == " 20%|\u258f|20/100"
    assert format_meter(
        20, 100, 12, ncols=14, rate=8.1,
        bar_format=r'{l_bar}{bar}|{n_fmt}/{total_fmt}') == " 20%|\u258d |20/100"
    # Check wide characters
    assert format_meter(0, 1000, 13, ncols=68, prefix='ｆｕｌｌｗｉｄｔｈ: ') == (
        "ｆｕｌｌｗｉｄｔｈ:   0%|                  | 0/1000 [00:13<?, ?it/s]")
    assert format_meter(0, 1000, 13, ncols=68, prefix='ニッポン [ﾆｯﾎﾟﾝ]: ') == (
        "ニッポン [ﾆｯﾎﾟﾝ]:   0%|                    | 0/1000 [00:13<?, ?it/s]")
    # Check that bar_format can print only {bar} or just one side
    assert format_meter(20, 100, 12, ncols=2, rate=8.1,
                        bar_format=r'{bar}') == "\u258d "
    assert format_meter(20, 100, 12, ncols=7, rate=8.1,
                        bar_format=r'{l_bar}{bar}') == " 20%|\u258d "
    assert format_meter(20, 100, 12, ncols=6, rate=8.1,
                        bar_format=r'{bar}|test') == "\u258f|test"
    # Check ncols trimming when `'{bar}' not in bar_format`
    long_desc = "x" * 50
    # no {bar}
    assert format_meter(1, 100, 12, ncols=10, bar_format="{desc}", prefix=long_desc) == "x" * 10
    # no total, no {bar}
    assert format_meter(1, None, 12, ncols=10, bar_format="{desc}", prefix=long_desc) == "x" * 10
    # no total, no bar_format (default stats line)
    assert len(format_meter(1, None, 12, ncols=10)) == 10
    # no trimming when ncols=0 or None
    assert format_meter(1, 100, 12, ncols=None, bar_format="{desc}", prefix=long_desc) == long_desc
    assert format_meter(1, None, 12, ncols=0, bar_format="{desc}", prefix=long_desc) == long_desc


def test_ANSI_escape_codes():
    ansi = {'BOLD': '\033[1m', 'RED': '\033[91m', 'END': '\033[0m'}
    desc_raw = '{BOLD}{RED}Colored{END} description'
    ncols = 123

    desc_stripped = desc_raw.format(BOLD='', RED='', END='')
    meter = tqdm.format_meter(0, 100, 0, ncols=ncols, prefix=desc_stripped)
    assert len(meter) == ncols

    desc = desc_raw.format(**ansi)
    meter = tqdm.format_meter(0, 100, 0, ncols=ncols, prefix=desc)
    # `format_meter` inserts an extra END for safety
    ansi_len = len(desc) - len(desc_stripped) + len(ansi['END'])
    assert len(meter) == ncols + ansi_len


def test_SI_format():
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
    assert '1.00Z ' in format_meter(1, 999999999999999999999, 1, unit_scale=True)
    assert '1.0Y ' in format_meter(1, 999999999999999999999999, 1, unit_scale=True)
    assert '10.0Y ' in format_meter(1, 9999999999999999999999999, 1, unit_scale=True)
    assert '100.0Y ' in format_meter(1, 99999999999999999999999999, 1, unit_scale=True)
    assert '1000.0Y ' in format_meter(1, 999999999999999999999999999, 1,
                                      unit_scale=True)


def test_bar_formatspec():
    """Test Bar.__format__ spec"""
    assert f"{Bar(0.3):5a}" == "#5   "
    assert f"{Bar(0.5, charset=' .oO0'):2}" == "0 "
    assert f"{Bar(0.5, charset=' .oO0'):2a}" == "# "
    assert f"{Bar(0.5, 10):-6a}" == '##  '
    assert f"{Bar(0.5, 10):2b}" == '  '


def test_no_kwargs(caperr):
    with tqdm(range(10)) as progressbar:
        assert len(progressbar) == 10
        for _ in progressbar:
            pass
    assert '10/10' in caperr()


class WriteTypeChecker(BytesIO):
    """File-like to assert the expected type is written"""
    def __init__(self, expected_type):
        super().__init__()
        self.expected_type = expected_type

    def write(self, s):
        assert isinstance(s, self.expected_type)


def test_native_string_io_for_default_file(monkeypatch):
    monkeypatch.setattr(sys, 'stderr', WriteTypeChecker(expected_type=str))
    for _ in tqdm(range(3)):
        pass
    sys.stderr.encoding = None  # unknown encoding
    for _ in tqdm(range(3)):
        pass


def test_unicode_string_io_for_specified_file():
    for _ in tqdm(range(3), file=WriteTypeChecker(expected_type=str)):
        pass


def test_write_bytes(monkeypatch):
    # specified file (and bytes)
    for _ in tqdm(range(3), file=WriteTypeChecker(expected_type=bytes),
                  write_bytes=True):
        pass
    # unspecified file (and unicode)
    monkeypatch.setattr(sys, 'stderr', WriteTypeChecker(expected_type=str))
    for _ in tqdm(range(3), write_bytes=False):
        pass


def test_iterate_over_csv_rows(tmp_file):
    writer = csv.writer(tmp_file)
    for _ in range(3):
        writer.writerow(['test'] * 3)
    tmp_file.seek(0)

    for _ in tqdm(csv.DictReader(tmp_file, fieldnames=('row1', 'row2', 'row3'))):
        pass


def test_file_output(tmp_file):
    for i in tqdm(range(3), file=tmp_file):
        if i == 1:
            tmp_file.seek(0)
            assert '0/3' in tmp_file.read()


def test_leave_option(caperr):
    """`leave=True` should print the final iteration"""
    for _ in tqdm(range(3), leave=True):
        pass
    res = caperr()
    assert '| 3/3 ' in res
    assert '\n' == res[-1]  # not '\r'

    for _ in tqdm(range(3), leave=False):
        pass
    assert '| 3/3 ' not in caperr()


def test_trange(caperr):
    for _ in trange(3, leave=True):
        pass
    assert '| 3/3 ' in caperr()

    for _ in trange(3, leave=False):
        pass
    assert '| 3/3 ' not in caperr()


def test_min_interval(caperr):
    for _ in tqdm(range(3), mininterval=1e-10):
        pass
    assert "  0%|          | 0/3 [00:00<" in caperr()


def test_max_interval(caperr, tmp_file, tmp_file2):
    total = 100
    bigstep = 10
    smallstep = 5

    # Test without maxinterval
    timer = DiscreteTimer()
    # with maxinterval but higher than loop sleep time
    t = tqdm(total=total, file=tmp_file, miniters=None, mininterval=0,
             smoothing=1, maxinterval=1e-2)
    cpu_timify(t, timer)

    # without maxinterval
    t2 = tqdm(total=total, file=tmp_file2, miniters=None, mininterval=0,
              smoothing=1, maxinterval=None)
    cpu_timify(t2, timer)

    assert t.dynamic_miniters
    assert t2.dynamic_miniters

    # Increase 10 iterations at once
    t.update(bigstep)
    t2.update(bigstep)
    # The next iterations should not trigger maxinterval (step 10)
    for _ in range(4):
        t.update(smallstep)
        t2.update(smallstep)
        timer.sleep(1e-5)
    t.close()  # because PyPy doesn't gc immediately
    t2.close()  # as above

    assert "25%" not in tmp_file.getvalue()
    assert "25%" not in tmp_file2.getvalue()

    # Test with maxinterval effect
    timer = DiscreteTimer()
    with tqdm(total=total, miniters=None, mininterval=0,
              smoothing=1, maxinterval=1e-4) as t:
        cpu_timify(t, timer)

        # Increase 10 iterations at once
        t.update(bigstep)
        # The next iterations should trigger maxinterval (step 5)
        for _ in range(4):
            t.update(smallstep)
            timer.sleep(1e-2)

        assert "25%" in caperr()

    # Test iteration based tqdm with maxinterval effect
    timer = DiscreteTimer()
    with tqdm(range(total), miniters=None,
              mininterval=1e-5, smoothing=1, maxinterval=1e-4) as t2:
        cpu_timify(t2, timer)

        for i in t2:
            if i >= (bigstep - 1) and ((i - (bigstep - 1)) % smallstep) == 0:
                timer.sleep(1e-2)
            if i >= 3 * bigstep:
                break

    assert "15%" in caperr()

    # Test different behavior with and without mininterval
    timer = DiscreteTimer()
    total = 1000
    mininterval = 0.1
    maxinterval = 10
    with tqdm(total=total, miniters=None, smoothing=1,
              mininterval=mininterval, maxinterval=maxinterval) as tm1:
        with tqdm(total=total, miniters=None, smoothing=1,
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
    t1 = tqdm(range(total), miniters=None, smoothing=1,
              mininterval=mininterval, maxinterval=maxinterval)
    t2 = tqdm(range(total), miniters=None, smoothing=1,
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


def test_delay(caperr):
    timer = DiscreteTimer()
    t = tqdm(total=2, leave=True, delay=3)
    cpu_timify(t, timer)
    timer.sleep(2)
    t.update(1)
    assert not caperr()
    timer.sleep(2)
    t.update(1)
    assert caperr()
    t.close()


def test_min_iters(caperr):
    for _ in tqdm(range(3), leave=True, mininterval=0, miniters=2):
        pass

    out = caperr()
    assert '| 0/3 ' in out
    assert '| 1/3 ' not in out
    assert '| 2/3 ' in out
    assert '| 3/3 ' in out

    for _ in tqdm(range(3), leave=True, mininterval=0, miniters=1):
        pass

    out = caperr()
    assert '| 0/3 ' in out
    assert '| 1/3 ' in out
    assert '| 2/3 ' in out
    assert '| 3/3 ' in out


def test_dynamic_min_iters(caperr):
    """Test purely dynamic miniters (and manual `update` & `__del__`)"""
    total = 10
    t = tqdm(total=total, miniters=None, mininterval=0, smoothing=1)

    t.update()
    # Increase 3 iterations
    t.update(3)
    # The next two iterations should be skipped because of dynamic_miniters
    t.update()
    t.update()
    # The third iteration should be displayed
    t.update()

    assert t.dynamic_miniters
    t.__del__()  # simulate immediate del gc

    out = caperr()
    assert '  0%|          | 0/10 [00:00<' in out
    assert '40%' in out
    assert '50%' not in out
    assert '60%' not in out
    assert '70%' in out

    # Check with smoothing=0, miniters should be set to max update seen so far
    t = tqdm(total=total, miniters=None, mininterval=0, smoothing=0)

    t.update()
    t.update(2)
    t.update(5)  # this should be stored as miniters
    t.update(1)

    out = caperr()
    assert all(i in out for i in ("0/10", "1/10", "3/10"))
    assert "2/10" not in out
    assert t.dynamic_miniters and not t.smoothing
    assert t.miniters == 5
    t.close()

    # Check iterable based tqdm
    t = tqdm(range(10), miniters=None, mininterval=None, smoothing=0.5)
    for _ in t:
        pass
    assert t.dynamic_miniters

    # No smoothing
    t = tqdm(range(10), miniters=None, mininterval=None, smoothing=0)
    for _ in t:
        pass
    assert t.dynamic_miniters

    # No dynamic_miniters (miniters is fixed manually)
    t = tqdm(range(10), miniters=1, mininterval=None)
    for _ in t:
        pass
    assert not t.dynamic_miniters


def test_big_min_interval(caperr):
    for _ in tqdm(range(2), mininterval=1E10):
        pass
    assert '50%' not in caperr()

    with tqdm(range(2), mininterval=1E10) as t:
        t.update()
        t.update()
        assert '50%' not in caperr()


def test_smoothed_dynamic_min_iters(caperr):
    timer = DiscreteTimer()

    with tqdm(total=100, miniters=None, mininterval=1,
              smoothing=0.5, maxinterval=0) as t:
        cpu_timify(t, timer)

        # Increase 10 iterations at once
        timer.sleep(1)
        t.update(10)
        # The next iterations should be partially skipped
        for _ in range(2):
            timer.sleep(1)
            t.update(4)
        for _ in range(20):
            timer.sleep(1)
            t.update()

        assert t.dynamic_miniters
    out = caperr()
    assert '  0%|          | 0/100 [00:00<' in out
    assert '20%' in out
    assert '23%' not in out
    assert '25%' in out
    assert '26%' not in out
    assert '28%' in out


def test_smoothed_dynamic_min_iters_with_min_interval(caperr):
    timer = DiscreteTimer()

    # In this test, `miniters` should gradually decline
    total = 100

    # Test manual updating tqdm
    with tqdm(total=total, miniters=None, mininterval=1e-3,
              smoothing=1, maxinterval=0) as t:
        cpu_timify(t, timer)

        t.update(10)
        timer.sleep(1e-2)
        for _ in range(4):
            t.update()
            timer.sleep(1e-2)
        out = caperr()
        assert t.dynamic_miniters

    # Test iteration-based tqdm
    with tqdm(range(total), miniters=None,
              mininterval=0.01, smoothing=1, maxinterval=0) as t2:
        cpu_timify(t2, timer)

        for i in t2:
            if i >= 10:
                timer.sleep(0.1)
            if i >= 14:
                break
        out2 = caperr()

    assert t.dynamic_miniters
    assert '  0%|          | 0/100 [00:00<' in out
    assert '11%' in out and '11%' in out2
    # assert '12%' not in out and '12%' in out2
    assert '13%' in out and '13%' in out2
    assert '14%' in out and '14%' in out2


def test_disable(caperr):
    for _ in tqdm(range(3), disable=True):
        pass
    assert not caperr()

    progressbar = tqdm(total=3, miniters=1, disable=True)
    progressbar.update(3)
    progressbar.close()
    assert not caperr()


def test_infinite_total():
    for _ in tqdm(range(3), total=float("inf")):
        pass


def test_nototal(caperr):
    for _ in tqdm(iter(range(10)), unit_scale=10):
        pass
    assert "100it" in caperr()

    for _ in tqdm(iter(range(10)), bar_format="{l_bar}{bar}{r_bar}"):
        pass
    assert "10/?" in caperr()


def test_SI_unit(caperr):
    for _ in tqdm(range(3), miniters=1, unit="bytes"):
        pass
    assert 'bytes/s' in caperr()


def test_ascii_autodetect(tmp_file):
    """Test ascii autodetection (`tmp_file` has no `encoding`)"""
    with tqdm(total=10, file=tmp_file, ascii=None) as t:
        assert t.ascii  # TODO: this may fail in the future
    assert tmp_file.encoding is None  # TODO: this may fail in the future


def test_ascii_bar(tmp_file):
    for _ in tqdm(range(3), total=15, file=tmp_file, miniters=1,
                  mininterval=0, ascii=True):
        pass
    res = tmp_file.getvalue().strip("\r").split("\r")
    assert '7%|6' in res[1]
    assert '13%|#3' in res[2]
    assert '20%|##' in res[3]


def test_unicode_bar():
    with UnicodeIO() as tmp_file:  # unlike `StringIO`, has an `encoding`
        assert tmp_file.encoding is not None
        with tqdm(total=15, file=tmp_file, ascii=False, mininterval=0) as t:
            for _ in range(3):
                t.update()
        res = tmp_file.getvalue().strip("\r").split("\r")
    assert "7%|\u258b" in res[1]
    assert "13%|\u2588\u258e" in res[2]
    assert "20%|\u2588\u2588" in res[3]


@mark.parametrize("bars", [" .oO0", " #"])
def test_custom_bar(tmp_file, bars):
    for _ in tqdm(range(len(bars) - 1), file=tmp_file, miniters=1,
                  mininterval=0, ascii=bars, ncols=27):
        pass
    for b, line in zip(bars, tmp_file.getvalue().strip("\r").split("\r")):
        assert '|' + b + '|' in line


def test_update(caperr):
    with tqdm(total=2, miniters=1, mininterval=0) as progressbar:
        assert len(progressbar) == 2
        progressbar.update(2)
        assert '| 2/2' in caperr()
        progressbar.desc = 'dynamically notify of 4 increments in total'
        progressbar.total = 4
        progressbar.update(-1)
        progressbar.update(2)
    res = caperr()
    assert '| 3/4 ' in res
    assert 'dynamically notify of 4 increments in total' in res


def test_close(caperr):
    # With `leave`
    progressbar = tqdm(total=3, miniters=10)
    progressbar.update(3)
    assert '| 3/3 ' not in caperr()  # Should be blank
    assert len(tqdm._instances) == 1
    progressbar.close()
    assert len(tqdm._instances) == 0
    assert '| 3/3 ' in caperr()

    # Without `leave`
    progressbar = tqdm(total=3, miniters=10, leave=False)
    progressbar.update(3)
    progressbar.close()
    assert '| 3/3 ' not in caperr()  # Should be blank

    # With all updates
    with tqdm(total=3, miniters=0, mininterval=0, leave=True) as progressbar:
        assert len(tqdm._instances) == 1
        progressbar.update(3)
        res = caperr()
        assert '| 3/3 ' in res  # Should be blank
        assert '\n' not in res
    # close() called
    assert len(tqdm._instances) == 0

    exres = res.rsplit(', ', 1)[0]
    res += caperr()
    assert res[-1] == '\n'
    assert res.startswith(exres)


def test_close_after_stream_closed(tmp_file):
    t = tqdm(total=2, file=tmp_file)
    t.update()
    t.update()
    tmp_file.close()
    t.close()


def test_ema():
    ema = EMA(0.01)
    assert round(ema(10), 2) == 10
    assert round(ema(1), 2) == 5.48
    assert round(ema(), 2) == 5.48
    assert round(ema(1), 2) == 3.97
    assert round(ema(1), 2) == 3.22


def smoothed_rates(smoothing, timer, tmp_file, tmp_file2):
    """Rates of an iterated and a manually updated bar, from empty `tmp_file`s"""
    for file in (tmp_file, tmp_file2):
        file.seek(0)
        file.truncate()
    kwargs = {'smoothing': smoothing, 'leave': True, 'miniters': 1, 'mininterval': 0}
    t = tqdm(range(3), file=tmp_file2, **kwargs)
    cpu_timify(t, timer)

    with tqdm(range(3), file=tmp_file, **kwargs) as t2:
        cpu_timify(t2, timer)

        for i in t2:
            # Sleep more for first iteration to see how quickly rate is updated.
            # Need to sleep in all iterations to calculate smoothed rate
            # (else delta_t is 0!)
            timer.sleep(0.01 if i == 0 else 0.001)
            t.update()
    n_old = len(tqdm._instances)
    t.close()
    assert len(tqdm._instances) == n_old - 1
    return (progressbar_rate(get_bar(tmp_file.getvalue(), 3)),
            progressbar_rate(get_bar(tmp_file2.getvalue(), 3)))


def test_smoothing(tmp_file, tmp_file2):
    timer = DiscreteTimer()

    # no smoothing
    with tqdm(range(3), file=tmp_file, smoothing=None, leave=True) as t:
        cpu_timify(t, timer)

        for _ in t:
            pass
    assert '| 3/3 ' in tmp_file.getvalue()

    a, a2 = smoothed_rates(None, timer, tmp_file, tmp_file2)  # average
    b, b2 = smoothed_rates(1, timer, tmp_file, tmp_file2)     # max (instant)
    c, c2 = smoothed_rates(0.5, timer, tmp_file, tmp_file2)   # medium

    # medium rate should be between average & max
    assert a <= c <= b
    assert a2 <= c2 <= b2


@mark.skipif(nt_and_no_colorama, reason="Windows without colorama")
def test_deprecated_nested(caperr):
    # TODO: test degradation on windows without colorama?
    with raises(TqdmDeprecationWarning):
        tqdm(total=2, nested=True)
    assert """`nested` is deprecated and automated.
Use `position` instead for manual control.""" in caperr()


def test_bar_format(caperr):
    bar_format = ('{l_bar}{bar}|{n_fmt}/{total_fmt}-{n}/{total}'
                  '{percentage}{rate}{rate_fmt}{elapsed}{remaining}')
    for _ in trange(2, leave=True, bar_format=bar_format):
        pass
    assert "\r  0%|          |0/2-0/20.0None?it/s00:00?\r" in caperr()

    # Test unicode string auto conversion
    with tqdm(ascii=False, bar_format=r'hello world') as t:
        assert isinstance(t.bar_format, str)


def test_custom_format(caperr):
    class TqdmExtraFormat(tqdm):
        """Provides a `total_time` format parameter"""
        @property
        def format_dict(self):
            d = super().format_dict
            total_time = d["elapsed"] * (d["total"] or 0) / max(d["n"], 1)
            d.update(total_time=self.format_interval(total_time) + " in total")
            return d

    for _ in TqdmExtraFormat(
            range(10), bar_format="{total_time}: {percentage:.0f}%|{bar}{r_bar}"):
        pass
    assert "00:00 in total" in caperr()


def test_eta(caperr):
    from datetime import datetime as dt
    for _ in trange(999, miniters=1, mininterval=0, leave=True,
                    bar_format='{l_bar}{eta:%Y-%m-%d}'):
        pass
    err = caperr()
    assert f"\r100%|{dt.now():%Y-%m-%d}\n" in err


def test_unpause(caperr):
    timer = DiscreteTimer()
    t = trange(10, leave=True, mininterval=0)
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
    bars = get_bar(caperr())
    assert progressbar_rate(bars[2]) == progressbar_rate(bars[3])


def test_disabled_unpause(capsys):
    with tqdm(total=10, disable=True) as t:
        t.update()
        t.unpause()
        t.update()
        print(t)
    out, err = capsys.readouterr()
    assert not err
    assert out == '  0%|          | 0/10 [00:00<?, ?it/s]\n'


def test_reset(caperr):
    with tqdm(total=10, miniters=1, mininterval=0, maxinterval=0) as t:
        t.update(9)
        t.reset()
        t.update()
        t.reset(total=12)
        t.update(10)
    err = caperr()
    assert '| 1/10' in err
    assert '| 10/12' in err


def test_reset_inf(caperr):
    with tqdm(total=10, miniters=1, mininterval=0, maxinterval=0) as t:
        t.update(5)
        t.reset(total=float("inf"))
        t.update()
        # same as tqdm(total=float("inf")): treated as unknown
        assert t.total is None
    err = caperr()
    assert '1it' in err


def test_disabled_reset(capsys):
    with tqdm(total=10, disable=True) as t:
        t.update(9)
        t.reset()
        t.update()
        t.reset(total=12)
        t.update(10)
        print(t)
    out, err = capsys.readouterr()
    assert not err
    assert out == '  0%|          | 0/12 [00:00<?, ?it/s]\n'


@mark.skipif(nt_and_no_colorama, reason="Windows without colorama")
def test_position(caperr):
    # Artificially test nested loop printing
    # Without leave
    kwargs = {'miniters': 1, 'mininterval': 0, 'maxinterval': 0}
    t = tqdm(total=2, desc='pos2 bar', leave=False, position=2, **kwargs)
    t.update()
    t.close()
    res = [m[0] for m in RE_pos.findall(caperr())]
    exres = ['\n\n\rpos2 bar:   0%',
             '\n\n\rpos2 bar:  50%',
             '\n\n\r      ']

    pos_line_diff(res, exres)

    # Test iteration-based tqdm positioning
    for _ in trange(2, desc='pos0 bar', position=0, **kwargs):
        for _ in trange(2, desc='pos1 bar', position=1, **kwargs):
            for _ in trange(2, desc='pos2 bar', position=2, **kwargs):
                pass
    res = [m[0] for m in RE_pos.findall(caperr())]
    exres = ['\rpos0 bar:   0%',
             '\n\rpos1 bar:   0%',
             '\n\n\rpos2 bar:   0%',
             '\n\n\rpos2 bar:  50%',
             '\n\n\rpos2 bar: 100%',
             '\rpos2 bar: 100%',
             '\n\n\rpos1 bar:  50%',
             '\n\n\rpos2 bar:   0%',
             '\n\n\rpos2 bar:  50%',
             '\n\n\rpos2 bar: 100%',
             '\rpos2 bar: 100%',
             '\n\n\rpos1 bar: 100%',
             '\rpos1 bar: 100%',
             '\n\rpos0 bar:  50%',
             '\n\rpos1 bar:   0%',
             '\n\n\rpos2 bar:   0%',
             '\n\n\rpos2 bar:  50%',
             '\n\n\rpos2 bar: 100%',
             '\rpos2 bar: 100%',
             '\n\n\rpos1 bar:  50%',
             '\n\n\rpos2 bar:   0%',
             '\n\n\rpos2 bar:  50%',
             '\n\n\rpos2 bar: 100%',
             '\rpos2 bar: 100%',
             '\n\n\rpos1 bar: 100%',
             '\rpos1 bar: 100%',
             '\n\rpos0 bar: 100%',
             '\rpos0 bar: 100%',
             '\n']
    pos_line_diff(res, exres)

    # Test manual tqdm positioning
    kwargs["total"] = 2
    t1 = tqdm(desc='pos0 bar', position=0, **kwargs)
    t2 = tqdm(desc='pos1 bar', position=1, **kwargs)
    t3 = tqdm(desc='pos2 bar', position=2, **kwargs)
    for _ in range(2):
        t1.update()
        t3.update()
        t2.update()
    res = [m[0] for m in RE_pos.findall(caperr())]
    exres = ['\rpos0 bar:   0%',
             '\n\rpos1 bar:   0%',
             '\n\n\rpos2 bar:   0%',
             '\rpos0 bar:  50%',
             '\n\n\rpos2 bar:  50%',
             '\n\rpos1 bar:  50%',
             '\rpos0 bar: 100%',
             '\n\n\rpos2 bar: 100%',
             '\n\rpos1 bar: 100%']
    pos_line_diff(res, exres)
    t1.close()
    t2.close()
    t3.close()
    caperr()  # discard closing bars

    # Test auto repositioning of bars when a bar is prematurely closed
    # tqdm._instances.clear()  # reset number of instances
    t1 = tqdm(total=10, desc='1.pos0 bar', mininterval=0)
    t2 = tqdm(total=10, desc='2.pos1 bar', mininterval=0)
    t3 = tqdm(total=10, desc='3.pos2 bar', mininterval=0)
    out = caperr()
    exres = ['\r1.pos0 bar:   0%',
             '\n\r2.pos1 bar:   0%',
             '\n\n\r3.pos2 bar:   0%']
    pos_line_diff([m[0] for m in RE_pos.findall(out)], exres)

    t2.close()
    t4 = tqdm(total=10, desc='4.pos2 bar', mininterval=0)
    t1.update(1)
    t3.update(1)
    t4.update(1)
    out += caperr()
    exres += ['\r2.pos1 bar:   0%',
              '\n\n\r4.pos2 bar:   0%',
              '\r1.pos0 bar:  10%',
              '\n\n\r3.pos2 bar:  10%',
              '\n\r4.pos2 bar:  10%']
    pos_line_diff([m[0] for m in RE_pos.findall(out)], exres)
    t4.close()
    t3.close()
    t1.close()


def test_set_description(caperr):
    with tqdm(desc='Hello') as t:
        assert t.desc == 'Hello'
        t.set_description_str('World')
        assert t.desc == 'World'
        t.set_description()
        assert t.desc == ''
        t.set_description('Bye')
        assert t.desc == 'Bye: '
    assert "World" in caperr()

    # without refresh
    with tqdm(desc='Hello') as t:
        assert t.desc == 'Hello'
        t.set_description_str('World', False)
        assert t.desc == 'World'
        t.set_description(None, False)
        assert t.desc == ''
    assert "World" not in caperr()

    # unicode
    with tqdm(total=10) as t:
        t.set_description("\xe1\xe9\xed\xf3\xfa")


@mark.parametrize("consume", [lambda t: t.update(1), list], ids=["update", "iter"])
def test_deprecated_gui(caperr, consume):
    """Test `gui=True` requires overriding `__iter__()` and `update()`"""
    t = tqdm(range(3), total=3, gui=True, miniters=1, mininterval=0)
    assert not hasattr(t, "sp")  # StatusPrinter iff gui is disabled
    try:
        with raises(TqdmDeprecationWarning):
            consume(t)
        assert ('Please use `tqdm.gui.tqdm(...)` instead of `tqdm(..., gui=True)`'
                in caperr())
    finally:
        t._instances.clear()


def test_gui_disabled():
    with tqdm(total=1, gui=False) as t:
        assert hasattr(t, "sp")


def test_cmp():
    t0 = tqdm(total=10)
    t1 = tqdm(total=10)
    t2 = tqdm(total=10)

    assert t0 < t1
    assert t2 >= t0
    assert t0 <= t2

    t3 = tqdm(total=10)
    t4 = tqdm(total=10)
    t5 = tqdm(total=10)
    t5.close()
    t6 = tqdm(total=10)

    assert t3 != t4
    assert t3 > t2
    assert t5 == t6
    t6.close()
    t4.close()
    t3.close()
    t2.close()
    t1.close()
    t0.close()


def test_repr():
    with tqdm(total=10, ascii=True) as t:
        assert str(t) == '  0%|          | 0/10 [00:00<?, ?it/s]'


def test_clear(caperr):
    t1 = tqdm(total=10, desc='pos0 bar', bar_format='{l_bar}')
    t2 = trange(10, desc='pos1 bar', bar_format='{l_bar}')
    out = caperr()
    before = squash_ctrlchars(out)
    t2.clear()
    t1.clear()
    after = squash_ctrlchars(out + caperr())
    t1.close()
    t2.close()
    assert before == ['pos0 bar:   0%|', 'pos1 bar:   0%|']
    assert after == ['', '']


def test_clear_disabled(caperr):
    with tqdm(total=10, desc='pos0 bar', disable=True, bar_format='{l_bar}') as t:
        t.clear()
    assert not caperr()


def test_refresh(caperr):
    t1 = tqdm(total=10, desc='pos0 bar',
              bar_format='{l_bar}', mininterval=999, miniters=999)
    t2 = tqdm(total=10, desc='pos1 bar',
              bar_format='{l_bar}', mininterval=999, miniters=999)
    t1.update()
    t2.update()
    out = caperr()
    before = squash_ctrlchars(out)
    t1.refresh()
    t2.refresh()
    after = squash_ctrlchars(out + caperr())
    t1.close()
    t2.close()

    # refreshing should force realtime state
    assert before == ['pos0 bar:   0%|', 'pos1 bar:   0%|']
    assert after == ['pos0 bar:  10%|', 'pos1 bar:  10%|']


def test_disabled_repr(capsys):
    with tqdm(total=10, disable=True) as t:
        str(t)
        t.update()
        print(t)
    out, err = capsys.readouterr()
    assert not err
    assert out == '  0%|          | 0/10 [00:00<?, ?it/s]\n'


def test_disabled_refresh(caperr):
    with tqdm(total=10, desc='pos0 bar', disable=True,
              bar_format='{l_bar}', mininterval=999, miniters=999) as t:
        t.update()
        t.refresh()

    assert not caperr()


def test_write(tmp_file):
    """Test bars are redrawn below written messages"""
    s = "Hello world"
    kwargs = {'file': tmp_file, 'bar_format': '{l_bar}', 'mininterval': 0, 'miniters': 1}
    t1 = tqdm(total=10, desc='pos0 bar', **kwargs)
    t2 = trange(10, desc='pos1 bar', **kwargs)
    t3 = tqdm(total=10, desc='pos2 bar', **kwargs)
    t1.update()
    t2.update()
    t3.update()
    before = tmp_file.getvalue()

    t1.write(s, file=tmp_file)  # call as an instance method
    tqdm.write(s, file=tmp_file)  # call as a class method
    after = tmp_file.getvalue()

    t1.close()
    t2.close()
    t3.close()

    assert squash_ctrlchars(after) == [s, s] + squash_ctrlchars(before)


def test_write_other_file(tmp_file, tmp_file2):
    """Test no bar clearing when writing to a different file"""
    with tqdm(total=10, file=tmp_file, desc='pos0 bar',
              bar_format='{l_bar}', mininterval=0, miniters=1) as t:
        t.update()
        before_bar = tmp_file.getvalue()
        tqdm.write("Hello world", file=tmp_file2)
        assert tmp_file.getvalue() == before_bar


def test_write_stdout_stderr(capsys):
    """Test stdout/stderr anti-mixup strategy"""
    s = "Hello world"
    t1 = tqdm(total=10, file=sys.stderr, desc='pos0 bar',
              bar_format='{l_bar}', mininterval=0, miniters=1)

    t1.update()
    before_out, before_err = capsys.readouterr()

    tqdm.write(s, file=sys.stdout)
    out, err = capsys.readouterr()
    after_out, after_err = before_out + out, before_err + err

    t1.close()

    assert before_err == '\rpos0 bar:   0%|\rpos0 bar:  10%|'
    assert before_out == ''
    pos_line_diff([m[0] for m in RE_pos.findall(after_err)],
                  ['\rpos0 bar:   0%|',
                   '\rpos0 bar:  10%|',
                   '\r               ',
                   '\r\rpos0 bar:  10%|'])
    assert after_out == s + '\n'


def test_len():
    """Test advance len (numpy array shape)"""
    np = importorskip('numpy')
    with tqdm(np.zeros((3, 4))) as t:
        assert len(t) == 3


def test_autodisable_nonTTY(caperr):
    with tqdm(total=10, disable=None) as t:
        t.update(3)
    assert not caperr()


def test_autoenable_TTY(tmp_file):
    tmp_file.isatty = lambda: True
    with tqdm(total=10, disable=None, file=tmp_file) as t:
        t.update()
    assert tmp_file.getvalue() != ''


def test_deprecation_exception(tmp_file):
    """Test `TqdmDeprecationWarning` with & without `fp_write`"""
    with raises(TqdmDeprecationWarning):
        raise TqdmDeprecationWarning('Test!', fp_write=tmp_file.write)
    assert "TqdmDeprecationWarning: Test!" in tmp_file.getvalue()

    with raises(TqdmDeprecationWarning, match="Test!"):
        raise TqdmDeprecationWarning('Test!', fp_write=None)


def test_postfix(caperr):
    postfix = {'float': 0.321034, 'gen': 543, 'str': 'h', 'lst': [2]}
    postfix_order = (('w', 'w'), ('a', 0))  # no need for OrderedDict
    expected = ['float=0.321', 'gen=543', 'lst=[2]', 'str=h']
    expected_order = ['w=w', 'a=0', 'float=0.321', 'gen=543', 'lst=[2]', 'str=h']

    # Test postfix set at init
    with tqdm(total=10, desc='pos0 bar', bar_format='{r_bar}', postfix=postfix) as t1:
        t1.refresh()
    out = caperr()

    # Test postfix set after init
    with trange(10, desc='pos1 bar', bar_format='{r_bar}', postfix=None) as t2:
        t2.set_postfix(**postfix)
        t2.refresh()
    out2 = caperr()

    # Order of items in dict may change, so need a loop to check per item
    for res in expected:
        assert res in out
        assert res in out2

    # Test postfix (with ordered dict and no refresh) set after init
    with trange(10, desc='pos2 bar', bar_format='{r_bar}', postfix=None) as t3:
        t3.set_postfix(postfix_order, False, **postfix)
        t3.refresh()  # explicit external refresh
        out3 = caperr()
    caperr()  # discard closing bar

    assert out3[1:-1].split(', ')[3:] == expected_order

    # Test postfix (with ordered dict and refresh) set after init
    with trange(10, desc='pos2 bar', bar_format='{r_bar}', postfix=None) as t4:
        t4.set_postfix(postfix_order, True, **postfix)
        t4.refresh()  # double refresh
        out4 = caperr()
    caperr()  # discard closing bar

    assert out4.count('\r') > out3.count('\r')
    assert out4.count(", ".join(expected_order)) == 2

    # Test setting postfix string directly
    with trange(10, desc='pos2 bar', bar_format='{r_bar}', postfix=None) as t5:
        t5.set_postfix_str("Hello", False)
        t5.set_postfix_str("World")
        out5 = caperr()

    assert "Hello" not in out5
    assert out5[1:-1].split(', ')[3:] == ["World"]


def test_postfix_direct(caperr):
    """Test directly assigning non-str objects to postfix"""
    with tqdm(total=10, miniters=1, mininterval=0,
              bar_format="{postfix[0][name]} {postfix[1]:>5.2f}",
              postfix=[{'name': "foo"}, 42]) as t:
        for i in range(10):
            if i % 2:
                t.postfix[0]["name"] = "abcdefghij"[i]
            else:
                t.postfix[1] = i
            t.update()
    res = caperr()
    assert "f  6.00" in res
    assert "h  6.00" in res
    assert "h  8.00" in res
    assert "j  8.00" in res


def test_file_redirection(tmp_file, monkeypatch):
    # Redirect stdout/stderr to tqdm.write()
    dummy = DummyTqdmFile(tmp_file)
    monkeypatch.setattr(sys, 'stdout', dummy)
    monkeypatch.setattr(sys, 'stderr', dummy)
    with tqdm(total=3) as pbar:
        print("Such fun")
        pbar.update(1)
        print("Such", "fun")
        pbar.update(1)
        print("Such ", end="")
        print("fun")
        pbar.update(1)
    res = tmp_file.getvalue()
    assert res.count("Such fun\n") == 3
    assert "0/3" in res
    assert "3/3" in res


def test_external_write(tmp_file):
    # Redirect stdout to tqdm.write()
    for _ in trange(3, file=tmp_file):
        del tqdm._lock  # classmethod should be able to recreate lock
        with tqdm.external_write_mode(file=tmp_file):
            tmp_file.write("Such fun\n")
    res = tmp_file.getvalue()
    assert res.count("Such fun\n") == 3
    assert "0/3" in res
    assert "3/3" in res


def test_numeric_unit_scale(caperr):
    for _ in tqdm(range(9), unit_scale=9, miniters=1, mininterval=0):
        pass
    assert '81/81' in caperr()


def test_threading(process_lock):
    """Test multiprocess/thread-realted features"""
    # TODO: test interleaved output #445


@mark.parametrize("disable", [False, True])
def test_bool(disable):
    kwargs = {'disable': disable}
    with trange(10, **kwargs) as t:
        assert t
    with trange(0, **kwargs) as t:
        assert not t
    with tqdm(total=10, **kwargs) as t:
        assert bool(t)
    with tqdm(total=0, **kwargs) as t:
        assert not bool(t)
    with tqdm([], **kwargs) as t:
        assert not t
    with tqdm([0], **kwargs) as t:
        assert t
    with tqdm(iter([]), **kwargs) as t:
        assert t
    with tqdm(iter([1, 2, 3]), **kwargs) as t:
        assert t
    with tqdm(**kwargs) as t:
        with raises(TypeError):
            bool(t)


@mark.parametrize("backend", ['auto', 'autonotebook'])
def test_auto(backend):
    module = import_module(f'tqdm.{backend}')
    with module.tqdm(total=10) as t:
        assert len(t) == 10
    with module.trange(1337) as t:
        assert len(t) == 1337


@mark.parametrize("as_bytes,expected", [(True, '%.1fB ['), (False, '%dit [')],
                  ids=["bytes", "iters"])
def test_wrapattr(caperr, tmp_file, as_bytes, expected):
    data = "a twenty-char string"
    with tqdm.wrapattr(tmp_file, "write", bytes=as_bytes) as wrap:
        wrap.write(data)
    assert tmp_file.getvalue() == data
    assert expected % len(data) in caperr()


def test_float_totals():
    with trange(10, total=9.6) as t:
        with warns(TqdmWarning, match="clamping frac") as record:
            for i in t:
                if i < 9:
                    assert not record


def test_screen_shape(caperr):
    # ncols
    with trange(10, ncols=50) as t:
        list(t)
    assert all(len(i) == 50 for i in get_bar(caperr()))

    # no second/third bar, leave=False
    kwargs = {'ncols': 50, 'nrows': 2, 'miniters': 0, 'mininterval': 0, 'leave': False}
    with trange(10, desc="one", **kwargs) as t1:
        with trange(10, desc="two", **kwargs) as t2:
            with trange(10, desc="three", **kwargs) as t3:
                list(t3)
            list(t2)
        list(t1)

    res = caperr()
    assert "one" in res
    assert "two" not in res
    assert "three" not in res
    assert "\n\n" not in res
    assert "more hidden" in res
    # double-check ncols
    assert all(len(i) == 50 for i in get_bar(res)
               if i.strip() and "more hidden" not in i)

    # all bars, leave=True
    del kwargs['leave']
    with trange(10, desc="one", **kwargs) as t1:
        with trange(10, desc="two", **kwargs) as t2:
            res = caperr()
            assert "two" not in res
            with trange(10, desc="three", **kwargs) as t3:
                res += caperr()
                assert "three" not in res
                list(t3)
            list(t2)
        list(t1)

    res += caperr()
    assert "one" in res
    assert "two" in res
    assert "three" in res
    assert "\n\n" not in res
    assert "more hidden" in res
    # double-check ncols
    assert all(len(i) == 50 for i in get_bar(res)
               if i.strip() and "more hidden" not in i)

    # second bar becomes first, leave=False
    kwargs['leave'] = False
    t1 = tqdm(total=10, desc="one", **kwargs)
    with tqdm(total=10, desc="two", **kwargs) as t2:
        t1.update()
        t2.update()
        t1.close()
        res = caperr()
        assert "one" in res
        assert "two" not in res
        assert "more hidden" in res
        t2.update()

    assert "two" in caperr()


def test_initial(caperr):
    for _ in tqdm(range(9), initial=10, total=19, miniters=1, mininterval=0):
        pass
    out = caperr()
    assert '10/19' in out
    assert '19/19' in out


@mark.parametrize("colour,ansi", [("#beefed", '\x1b[38;2;%d;%d;%dm' % (0xbe, 0xef, 0xed)),
                                  ("blue", '\x1b[34m')])
def test_colour(caperr, colour, ansi):
    for _ in tqdm(range(9), colour=colour):
        pass
    assert ansi in caperr()


def test_colour_unknown():
    with warns(TqdmWarning, match="Unknown colour") as record:
        with tqdm(total=1, colour="charm") as t:
            assert record  # warned on construction
            t.update()


def test_closed_file(tmp_file):
    for i in trange(9, file=tmp_file, miniters=1, mininterval=0):
        if i == 5:
            tmp_file.close()


def test_reversed(caperr):
    for _ in reversed(tqdm(range(9))):
        pass
    err = caperr()
    assert '  0%' in err
    assert '100%' in err


def test_contains(caperr):
    """Test __contains__ doesn't iterate"""
    with tqdm(list(range(9))) as t:
        assert 9 not in t
        assert all(i in t for i in range(9))
    err = caperr()
    assert '  0%' in err
    assert '100%' not in err


def test_write_stdout_none(monkeypatch):
    monkeypatch.setattr(sys, 'stdout', None)
    tqdm.write("should do nothing")
