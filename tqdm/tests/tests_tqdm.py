# Advice: use repr(our_file.read()) to print the full output of tqdm
# (else '\r' will replace the previous lines and you'll see only the latest.

from __future__ import unicode_literals

import csv
import re

from tqdm import tqdm
from tqdm import trange

try:
    from StringIO import StringIO
except:
    from io import StringIO

from io import IOBase  # to support unicode strings

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


class DiscreteTimer(object):
    '''Virtual discrete time manager, to precisely control time for tests'''

    def __init__(self):
        self.t = 0.0

    def sleep(self, t):
        '''Sleep = increment the time counter (almost no CPU used)'''
        self.t += t

    def time(self):
        '''Get the current time'''
        return self.t


def cpu_timify(t, timer=None):
    '''Force tqdm to use the specified timer instead of system-wide time()'''
    if timer is None:
        timer = DiscreteTimer()
    t._time = timer.time
    t.start_t = t.last_print_t = t._time()
    return timer


class UnicodeIO(IOBase):
    ''' Unicode version of StringIO '''

    def __init__(self, *args, **kwargs):
        super(UnicodeIO, self).__init__(*args, **kwargs)
        self.encoding = 'U8'  # io.StringIO supports unicode, but no encoding
        self.text = ''
        self.cursor = 0
    
    def seek(self, offset):
        self.cursor = offset

    def tell(self):
        return self.cursor

    def write(self, s):
        self.text += s
        self.cursor = len(self.text)

    def read(self):
        return self.text[self.cursor:]

    def getvalue(self):
        return self.text


def get_bar(all_bars, i):
    """ Get a specific update from a whole bar traceback """
    return all_bars.strip('\r').split('\r')[i]


RE_rate = re.compile(r'(\d+\.\d+)it/s')

def progressbar_rate(bar_str):
    return float(RE_rate.search(bar_str).group(1))


def test_format_interval():
    """ Test time interval format """
    format_interval = tqdm.format_interval
    assert format_interval(60) == '01:00'
    assert format_interval(6160) == '1:42:40'
    assert format_interval(238113) == '66:08:33'


def test_format_meter():
    """ Test statistics and progress bar formatting """
    try:
        unich = unichr
    except NameError:
        unich = chr

    format_meter = tqdm.format_meter

    assert format_meter(0, 1000, 13) == \
        "  0%|          | 0/1000 [00:13<?,  0.00it/s]"
    assert format_meter(0, 1000, 13, ncols=68, prefix='desc: ') == \
        "desc:   0%|                            | 0/1000 [00:13<?,  0.00it/s]"
    assert format_meter(231, 1000, 392) == \
        " 23%|" + unich(0x2588) * 2 + unich(0x258e) + \
        "       | 231/1000 [06:32<21:44,  1.70s/it]"
    assert format_meter(10000, 1000, 13) == \
        "10000it [00:13, 769.23it/s]"
    assert format_meter(231, 1000, 392, ncols=56, ascii=True) == \
        " 23%|" + '#' * 3 + '6' + \
        "            | 231/1000 [06:32<21:44,  1.70s/it]"
    assert format_meter(100000, 1000, 13, unit_scale=True, unit='iB') == \
        "100KiB [00:13, 7.69KiB/s]"
    assert format_meter(100, 1000, 12, ncols=0, rate=7.33) == \
        " 10% 100/1000 [00:12<02:02,  7.33it/s]"
    assert format_meter(20, 100, 12, ncols=30, rate=8.1,
                        bar_format=r'{l_bar}{bar}|{n_fmt}/{total_fmt}') == \
        " 20%|" + unich(0x258f) + "|20/100"


def test_si_format():
    """ Test SI unit prefixes """
    format_meter = tqdm.format_meter

    assert '9.00 ' in format_meter(1, 9, 1, unit_scale=True, unit='B')
    assert '99.0 ' in format_meter(1, 99, 1, unit_scale=True)
    assert '999 ' in format_meter(1, 999, 1, unit_scale=True)
    assert '9.99K ' in format_meter(1, 9994, 1, unit_scale=True)
    assert '10.0K ' in format_meter(1, 9999, 1, unit_scale=True)
    assert '99.5K ' in format_meter(1, 99499, 1, unit_scale=True)
    assert '100K ' in format_meter(1, 99999, 1, unit_scale=True)
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


def test_all_defaults():
    """ Test default kwargs """
    with closing(UnicodeIO()) as our_file:
        progressbar = tqdm(range(10), file=our_file)
        assert len(progressbar) == 10
        for _ in progressbar:
            pass


def test_iterate_over_csv_rows():
    """ Test csv iterator """
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
            for row in tqdm(reader, file=our_file):
                pass


def test_file_output():
    """ Test output to arbitrary file-like objects """
    with closing(StringIO()) as our_file:
        for i in tqdm(_range(3), file=our_file):
            if i == 1:
                our_file.seek(0)
                assert '0/3' in our_file.read()


def test_leave_option():
    """ Test `leave=True` always prints info about the last iteration """
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


def test_trange():
    """ Test trange """
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


def test_min_interval():
    """ Test mininterval """
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(3), file=our_file, mininterval=1e-10):
            pass
        our_file.seek(0)
        assert "  0%|          | 0/3 [00:00<" in our_file.read()


def test_max_interval():
    """ Test maxinterval """
    total = 100
    bigstep = 10
    smallstep = 5
    timer = DiscreteTimer()

    # Test without maxinterval
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

            our_file.seek(0)
            our_file2.seek(0)
            out = our_file.read()
            out2 = our_file2.read()
            assert "25%" not in out
            assert "25%" not in out2

    # Test with maxinterval effect
    with closing(StringIO()) as our_file:
        t = tqdm(total=total, file=our_file, miniters=None, mininterval=0,
                 smoothing=1, maxinterval=1e-4)
        cpu_timify(t, timer)

        # Increase 10 iterations at once
        t.update(bigstep)
        # The next iterations should trigger maxinterval (step 5)
        for _ in _range(4):
            t.update(smallstep)
            timer.sleep(1e-2)

        our_file.seek(0)
        out = our_file.read()
        assert "25%" in out

    # Test iteration based tqdm with maxinterval effect
    with closing(StringIO()) as our_file:
        t2 = tqdm(_range(total), file=our_file, miniters=None,
                  mininterval=1e-5, smoothing=1, maxinterval=1e-4)
        cpu_timify(t2, timer)

        for i in t2:
            if i >= (bigstep - 1) and ((i - (bigstep - 1)) % smallstep) == 0:
                timer.sleep(1e-2)
            if i >= 3 * bigstep:
                break

        our_file.seek(0)
        out = our_file.read()
        assert "15%" in out


def test_min_iters():
    """ Test miniters """
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


def test_dynamic_min_iters():
    """ Test purely dynamic miniters """
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
        assert '  0%|          | 0/10 [00:00<' in out
        assert '40%' in out
        assert '50%' not in out
        assert '60%' not in out
        assert '70%' in out

    with closing(StringIO()) as our_file:
        t = tqdm(_range(10), file=our_file, miniters=None, mininterval=None)
        for _ in t:
            pass
        assert t.dynamic_miniters

    with closing(StringIO()) as our_file:
        t = tqdm(_range(10), file=our_file, miniters=1, mininterval=None)
        for _ in t:
            pass
        assert not t.dynamic_miniters


def test_big_min_interval():
    """ Test large mininterval """
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(2), file=our_file, mininterval=1E10):
            pass
        our_file.seek(0)
        assert '50%' not in our_file.read()

    with closing(StringIO()) as our_file:
        t = tqdm(_range(2), file=our_file, mininterval=1E10)
        t.update()
        t.update()
        our_file.seek(0)
        assert '50%' not in our_file.read()


def test_smoothed_dynamic_min_iters():
    """ Test smoothed dynamic miniters """
    timer = DiscreteTimer()

    with closing(StringIO()) as our_file:
        total = 100
        t = tqdm(total=total, file=our_file, miniters=None, mininterval=0,
                 smoothing=0.5, maxinterval=0)
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


def test_smoothed_dynamic_min_iters_with_min_interval():
    """ Test smoothed dynamic miniters with mininterval """
    timer = DiscreteTimer()

    # Basically in this test, miniters should gradually decline
    with closing(StringIO()) as our_file:
        total = 100

        # Test manual updating tqdm
        t = tqdm(total=total, file=our_file, miniters=None, mininterval=1e-3,
                 smoothing=1, maxinterval=0)
        cpu_timify(t, timer)

        t.update(10)
        timer.sleep(1e-2)
        for _ in _range(4):
            t.update()
            timer.sleep(1e-2)
        our_file.seek(0)
        out = our_file.read()

    with closing(StringIO()) as our_file:
        # Test iteration-based tqdm
        t2 = tqdm(_range(total), file=our_file, miniters=None,
                  mininterval=0.01, smoothing=1, maxinterval=0)
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


def test_disable():
    """ Test disable """
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


def test_unit():
    """ Test SI unit prefix """
    with closing(StringIO()) as our_file:
        for _ in tqdm(_range(3), file=our_file, miniters=1, unit="bytes"):
            pass
        our_file.seek(0)
        assert 'bytes/s' in our_file.read()


def test_ascii():
    """ Test ascii/unicode bar """
    # Test ascii autodetection
    with closing(StringIO()) as our_file:
        t = tqdm(total=10, file=our_file, ascii=None)
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
        t = tqdm(total=15, file=our_file, ascii=False, mininterval=0)
        for _ in _range(3):
            t.update()
        our_file.seek(0)
        res = our_file.read().strip("\r").split("\r")
        assert "7%|\u258b" in res[1]
        assert "13%|\u2588\u258e" in res[2]
        assert "20%|\u2588\u2588" in res[3]


def test_update():
    """ Test manual creation and updates """
    with closing(StringIO()) as our_file:
        progressbar = tqdm(total=2, file=our_file, miniters=1, mininterval=0)
        assert len(progressbar) == 2
        progressbar.update(2)
        our_file.seek(0)
        assert '| 2/2' in our_file.read()
        progressbar.desc = 'dynamically notify of 4 increments in total'
        progressbar.total = 4
        try:
            progressbar.update(-10)
        except ValueError as e:
            if str(e) != "n (-10) cannot be less than 1":
                raise
            progressbar.update()  # should default to +1
        else:
            raise ValueError("Should not support negative updates")
        our_file.seek(0)
        assert '| 3/4 ' in our_file.read()
        our_file.seek(0)
        assert 'dynamically notify of 4 increments in total' in our_file.read()


def test_close():
    """ Test manual creation and closure """
    # With `leave` option
    with closing(StringIO()) as our_file:
        progressbar = tqdm(total=3, file=our_file, miniters=10, leave=True)
        progressbar.update(3)
        assert '| 3/3 ' not in our_file.getvalue()  # Should be blank
        progressbar.close()
        assert '| 3/3 ' in our_file.getvalue()

    # Without `leave` option
    with closing(StringIO()) as our_file:
        progressbar = tqdm(total=3, file=our_file, miniters=10, leave=False)
        progressbar.update(3)
        progressbar.close()
        assert '| 3/3 ' not in our_file.getvalue()  # Should be blank

    # With all updates
    with closing(StringIO()) as our_file:
        with tqdm(total=3, file=our_file, miniters=0, mininterval=0,
                  leave=True) as progressbar:
            progressbar.update(3)
            res = our_file.getvalue()
            assert '| 3/3 ' in res  # Should be blank
        # close() called
        try:
            assert res + '\n' == our_file.getvalue()
        except AssertionError:
            raise AssertionError('\n'.join(
                ('expected extra line (\\n) after `close`:',
                 'before:', repr(res), 'closed:', repr(our_file.getvalue()), 'end debug\n')))


def test_smoothing():
    """ Test exponential weighted average smoothing """
    timer = DiscreteTimer()

    # -- Test disabling smoothing
    with closing(StringIO()) as our_file:
        t = tqdm(_range(3), file=our_file, smoothing=None, leave=True)
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

            t2 = tqdm(_range(3), file=our_file, smoothing=None, leave=True,
                      miniters=1, mininterval=0)
            cpu_timify(t2, timer)

            for i in t2:
                # Sleep more for first iteration and
                # see how quickly rate is updated
                if i == 0:
                    timer.sleep(0.01)
                else:
                    # Need to sleep in all iterations to calculate smoothed rate
                    # (else delta_t is 0!)
                    timer.sleep(0.001)
                t.update()
            # Get result for iter-based bar
            our_file.seek(0)
            a = progressbar_rate(get_bar(our_file.read(), 3))
        # Get result for manually updated bar
        our_file2.seek(0)
        a2 = progressbar_rate(get_bar(our_file2.read(), 3))

    # 2nd case: use max smoothing (= instant rate)
    with closing(StringIO()) as our_file2:
        with closing(StringIO()) as our_file:
            t = tqdm(_range(3), file=our_file2, smoothing=1, leave=True,
                     miniters=1, mininterval=0)
            cpu_timify(t, timer)

            t2 = tqdm(_range(3), file=our_file, smoothing=1, leave=True,
                      miniters=1, mininterval=0)
            cpu_timify(t2, timer)

            for i in t2:
                if i == 0:
                    timer.sleep(0.01)
                else:
                    timer.sleep(0.001)
                t.update()
            # Get result for iter-based bar
            our_file.seek(0)
            b = progressbar_rate(get_bar(our_file.read(), 3))
        # Get result for manually updated bar
        our_file2.seek(0)
        b2 = progressbar_rate(get_bar(our_file2.read(), 3))

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
            # Get result for iter-based bar
            our_file.seek(0)
            c = progressbar_rate(get_bar(our_file.read(), 3))
        # Get result for manually updated bar
        our_file2.seek(0)
        c2 = progressbar_rate(get_bar(our_file2.read(), 3))

    # Check that medium smoothing's rate is between no and max smoothing rates
    assert a < c < b
    assert a2 < c2 < b2


def test_nested():
    """ Test nested progress bars """
    # Use regexp because the it rates can change
    RE_nested = re.compile(r'((\x1b\[A|\r|\n)+((outer|inner) loop:\s+\d+%|\s{3,6})?)')  # NOQA
    RE_nested2 = re.compile(r'((\x1b\[A|\r|\n)+((outer0|inner1|inner2) loop:\s+\d+%|\s{3,6})?)')  # NOQA

    # Artificially test nested loop printing
    # Without leave
    our_file = StringIO()
    t = tqdm(total=2, file=our_file, miniters=1, mininterval=0,
             maxinterval=0, desc='inner loop', leave=False, nested=True)
    t.update()
    t.close()
    our_file.seek(0)
    out = our_file.read()
    res = [m[0] for m in RE_nested.findall(out)]
    assert res == ['\n\rinner loop:   0%',
                   '\rinner loop:  50%',
                   '\r      ',
                   '\r\x1b[A']

    # With leave
    our_file = StringIO()
    t = tqdm(total=2, file=our_file, miniters=1, mininterval=0,
             maxinterval=0, desc='inner loop', leave=True, nested=True)
    t.update()
    t.close()
    our_file.seek(0)
    out = our_file.read()
    res = [m[0] for m in RE_nested.findall(out)]
    assert res == ['\n\rinner loop:   0%',
                   '\rinner loop:  50%',
                   '\r\x1b[A']

    # Test simple nested, without leave
    our_file = StringIO()
    for i in trange(2, file=our_file, miniters=1, mininterval=0,
                    maxinterval=0, desc='outer loop', leave=True):
        for j in trange(4, file=our_file, miniters=1, mininterval=0,
                        maxinterval=0, desc='inner loop', leave=False,
                        nested=True):
            pass
    our_file.seek(0)
    out = our_file.read()
    res = [m[0] for m in RE_nested.findall(out)]
    assert res == ['\router loop:   0%',
                   '\n\rinner loop:   0%',
                   '\rinner loop:  25%',
                   '\rinner loop:  50%',
                   '\rinner loop:  75%',
                   '\rinner loop: 100%',
                   '\r      ',
                   '\r\x1b[A\router loop:  50%',
                   '\n\rinner loop:   0%',
                   '\rinner loop:  25%',
                   '\rinner loop:  50%',
                   '\rinner loop:  75%',
                   '\rinner loop: 100%',
                   '\r      ',
                   '\r\x1b[A\router loop: 100%',
                   '\n']

    # Test nested with leave
    our_file = StringIO()
    for i in trange(2, file=our_file, miniters=1, mininterval=0,
                    maxinterval=0, desc='outer loop', leave=True):
        for j in trange(4, file=our_file, miniters=1, mininterval=0,
                        maxinterval=0, desc='inner loop', leave=True,
                        nested=True):
            pass
    our_file.seek(0)
    out = our_file.read()
    res = [m[0] for m in RE_nested.findall(out)]
    assert res == ['\router loop:   0%',
                   '\n\rinner loop:   0%',
                   '\rinner loop:  25%',
                   '\rinner loop:  50%',
                   '\rinner loop:  75%',
                   '\rinner loop: 100%',
                   '\r\x1b[A\router loop:  50%',
                   '\n\rinner loop:   0%',
                   '\rinner loop:  25%',
                   '\rinner loop:  50%',
                   '\rinner loop:  75%',
                   '\rinner loop: 100%',
                   '\r\x1b[A\router loop: 100%',
                   '\n']

    # Test 2 nested loops with leave
    our_file = StringIO()
    for i in trange(2, file=our_file, miniters=1, mininterval=0,
                    maxinterval=0, desc='outer0 loop', leave=True):
        for j in trange(2, file=our_file, miniters=1, mininterval=0,
                        maxinterval=0, desc='inner1 loop', leave=True,
                        nested=True):
            for k in trange(2, file=our_file, miniters=1, mininterval=0,
                            maxinterval=0, desc='inner2 loop', leave=True,
                            nested=True):
                pass
    our_file.seek(0)
    out = our_file.read()
    res = [m[0] for m in RE_nested2.findall(out)]
    assert res == ['\router0 loop:   0%',
                   '\n\rinner1 loop:   0%',
                   '\n\rinner2 loop:   0%',
                   '\rinner2 loop:  50%',
                   '\rinner2 loop: 100%',
                   '\r\x1b[A\rinner1 loop:  50%',
                   '\n\rinner2 loop:   0%',
                   '\rinner2 loop:  50%',
                   '\rinner2 loop: 100%',
                   '\r\x1b[A\rinner1 loop: 100%',
                   '\r\x1b[A\router0 loop:  50%',
                   '\n\rinner1 loop:   0%',
                   '\n\rinner2 loop:   0%',
                   '\rinner2 loop:  50%',
                   '\rinner2 loop: 100%',
                   '\r\x1b[A\rinner1 loop:  50%',
                   '\n\rinner2 loop:   0%',
                   '\rinner2 loop:  50%',
                   '\rinner2 loop: 100%',
                   '\r\x1b[A\rinner1 loop: 100%',
                   '\r\x1b[A\router0 loop: 100%',
                   '\n']
    # TODO: test degradation on windows without colorama?


def test_bar_format():
    ''' Test custom bar formatting'''
    with closing(StringIO()) as our_file:
        bar_format = r'{l_bar}{bar}|{n_fmt}/{total_fmt}-{n}/{total}{percentage}{rate}{rate_fmt}{elapsed}{remaining}'  # NOQA
        for i in trange(2, file=our_file, leave=True, bar_format=bar_format):
            pass
        out = our_file.getvalue()
        assert "\r  0%|          |0/2-0/20.0None?it/s00:00?\r" in out

        # Test unicode string auto conversion
        bar_format = r'hello world'
        t = tqdm(file=our_file, ascii=False, bar_format=bar_format)
        assert isinstance(t.bar_format, _unicode)


def test_unpause():
    """ Test unpause """
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


def test_set_description():
    """ Test set description """
    with closing(StringIO()) as our_file:
        t = tqdm(file=our_file, desc='Hello')
        assert t.desc == 'Hello: '
        t.set_description('World')
        assert t.desc == 'World: '
        t.set_description()
        assert t.desc == ''


def test_no_gui():
    """ Test internal GUI properties """
    # Check: StatusPrinter iff gui is disabled
    with closing(StringIO()) as our_file:
        t = tqdm(total=2, gui=True, file=our_file, miniters=1, mininterval=0)
        assert not hasattr(t, "sp")
        try:
            t.update(1)
        except DeprecationWarning:
            pass
        else:
            raise DeprecationWarning('Should not allow manual gui=True without'
                                     ' overriding __iter__() and update()')

        try:
            for _ in tqdm(_range(3), gui=True, file=our_file,
                          miniters=1, mininterval=0):
                pass
        except DeprecationWarning:
            pass
        else:
            raise DeprecationWarning('Should not allow manual gui=True without'
                                     ' overriding __iter__() and update()')

        t = tqdm(total=1, gui=False, file=our_file)
        assert hasattr(t, "sp")
