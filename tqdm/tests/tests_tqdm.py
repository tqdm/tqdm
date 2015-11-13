from __future__ import unicode_literals

import csv
import re
from time import sleep

try:
    _range = xrange
except NameError:
    _range = range

try:
    from StringIO import StringIO
except:
    from io import StringIO
from io import StringIO as uIO  # supports unicode strings

from tqdm import format_interval
from tqdm import format_meter
from tqdm import tqdm
from tqdm import trange


def test_format_interval():
    """ Test time interval format """
    assert format_interval(60) == '01:00'
    assert format_interval(6160) == '1:42:40'
    assert format_interval(238113) == '66:08:33'


def test_format_meter():
    """ Test statistics and progress bar formatting """
    try:
        unich = unichr
    except NameError:
        unich = chr

    assert format_meter(0, 1000, 13) == \
        "  0%|          | 0/1000 [00:13<?,  0.00it/s]"
    assert format_meter(0, 1000, 13, ncols=68, prefix='desc: ') == \
        "desc:   0%|                            | 0/1000 [00:13<?,  0.00it/s]"
    assert format_meter(231, 1000, 392) == \
        " 23%|" + unich(0x2588) * 2 + unich(0x258e) + \
        "       | 231/1000 [06:32<21:44,  0.59it/s]"
    assert format_meter(10000, 1000, 13) == \
        "10000it [00:13, 769.23it/s]"
    assert format_meter(231, 1000, 392, ncols=56, ascii=True) == \
        " 23%|" + '#' * 3 + '6' + \
        "            | 231/1000 [06:32<21:44,  0.59it/s]"
    assert format_meter(100000, 1000, 13, unit_scale=True, unit='iB') == \
        "100KiB [00:13, 7.69KiB/s]"
    assert format_meter(100, 1000, 12, ncols=0, rate=7.33) == \
        " 10% 100/1000 [00:12<02:02,  7.33it/s]"


def test_si_format():
    """ Test SI unit prefixes """
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
    progressbar = tqdm(range(10))
    assert len(progressbar) == 10
    for i in progressbar:
        pass
    import sys
    sys.stderr.write('tests_tqdm.test_all_defaults ... ')


def test_iterate_over_csv_rows():
    """ Test csv iterator """
    # Create a test csv pseudo file
    test_csv_file = StringIO()
    writer = csv.writer(test_csv_file)
    for i in _range(3):
        writer.writerow(['test'] * 3)
    test_csv_file.seek(0)

    # Test that nothing fails if we iterate over rows
    reader = csv.DictReader(test_csv_file, fieldnames=('row1', 'row2', 'row3'))
    our_file = StringIO()
    for row in tqdm(reader, file=our_file):
        pass
    our_file.close()


def test_file_output():
    """ Test output to arbitrary file-like objects """
    our_file = StringIO()
    for i in tqdm(_range(3), file=our_file):
        if i == 1:
            our_file.seek(0)
            assert '0/3' in our_file.read()


def test_leave_option():
    """ Test `leave=True` always prints info about the last iteration """
    our_file = StringIO()
    for i in tqdm(_range(3), file=our_file, leave=True):
        pass
    our_file.seek(0)
    assert '| 3/3 ' in our_file.read()
    our_file.seek(0)
    assert '\n' == our_file.read()[-1]  # not '\r'
    our_file.close()

    our_file2 = StringIO()
    for i in tqdm(_range(3), file=our_file2, leave=False):
        pass
    our_file2.seek(0)
    assert '| 3/3 ' not in our_file2.read()
    our_file2.close()


def test_trange():
    """ Test trange """
    our_file = StringIO()
    for i in trange(3, file=our_file, leave=True):
        pass
    our_file.seek(0)
    assert '| 3/3 ' in our_file.read()
    our_file.close()

    our_file2 = StringIO()
    for i in trange(3, file=our_file2, leave=False):
        pass
    our_file2.seek(0)
    assert '| 3/3 ' not in our_file2.read()
    our_file2.close()


def test_min_interval():
    """ Test mininterval """
    our_file = StringIO()
    for i in tqdm(_range(3), file=our_file, mininterval=1e-10):
        pass
    our_file.seek(0)
    assert "  0%|          | 0/3 [00:00<" in our_file.read()
    our_file.close()


def test_min_iters():
    """ Test miniters """
    our_file = StringIO()
    for i in tqdm(_range(3), file=our_file, leave=True, miniters=4):
        our_file.write('blank\n')
    our_file.seek(0)
    assert '\nblank\nblank\n' in our_file.read()
    our_file.close()

    our_file2 = StringIO()
    for i in tqdm(_range(3), file=our_file2, leave=True, miniters=1):
        our_file2.write('blank\n')
    our_file2.seek(0)
    # assume automatic mininterval = 0 means intermediate output
    assert '| 3/3 ' in our_file2.read()
    our_file2.close()


def test_dynamic_min_iters():
    """ Test purely dynamic miniters """
    our_file = StringIO()
    total = 10
    t = tqdm(total=total, file=our_file, miniters=None, mininterval=0)

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

    our_file = StringIO()
    t = tqdm(_range(10), file=our_file, miniters=None, mininterval=None)
    for i in t:
        pass
    assert t.dynamic_miniters

    our_file = StringIO()
    t = tqdm(_range(10), file=our_file, miniters=1, mininterval=None)
    for i in t:
        pass
    assert not t.dynamic_miniters

    our_file.close()


def test_big_min_interval():
    """ Test large mininterval """
    our_file = StringIO()
    for i in tqdm(_range(2), file=our_file, mininterval=1E10):
        pass
    our_file.seek(0)
    assert '50%' not in our_file.read()

    our_file = StringIO()
    t = tqdm(_range(2), file=our_file, mininterval=1E10)
    t.update()
    t.update()
    our_file.seek(0)
    assert '50%' not in our_file.read()

    our_file.close()


def test_disable():
    """ Test disable """
    our_file = StringIO()
    for i in tqdm(_range(3), file=our_file, disable=True):
        pass
    our_file.seek(0)
    assert our_file.read() == ''

    our_file2 = StringIO()
    progressbar = tqdm(total=3, file=our_file2, miniters=1, disable=True)
    progressbar.update(3)
    progressbar.close()
    our_file2.seek(0)
    assert our_file2.read() == ''


def test_unit():
    """ Test SI unit prefix """
    our_file = StringIO()
    for i in tqdm(_range(3), file=our_file, miniters=1, unit="bytes"):
        pass
    our_file.seek(0)
    assert 'bytes/s' in our_file.read()
    our_file.close()


def test_ascii():
    """ Test ascii/unicode bar """
    # Test ascii autodetection
    our_file = StringIO()
    t = tqdm(total=10, file=our_file, ascii=None)
    assert t.ascii  # TODO: this may fail in the future
    our_file.close()

    # Test ascii bar
    our_file = StringIO()
    for i in tqdm(_range(3), total=15, file=our_file, miniters=1, mininterval=0,
                  ascii=True):
        pass
    our_file.seek(0)
    res = our_file.read().strip("\r").split("\r")
    our_file.close()
    assert '7%|6' in res[1]
    assert '13%|#3' in res[2]
    assert '20%|##' in res[3]

    # Test unicode bar
    our_file = uIO()
    t = tqdm(total=15, file=our_file, ascii=False, mininterval=0)
    for i in _range(3):
        t.update()
    our_file.seek(0)
    res = our_file.read().strip("\r").split("\r")
    our_file.close()
    assert "7%|\u258b" in res[1]
    assert "13%|\u2588\u258e" in res[2]
    assert "20%|\u2588\u2588" in res[3]


def test_update():
    """ Test manual creation and updates """
    our_file = StringIO()
    progressbar = tqdm(total=2, file=our_file, miniters=1, mininterval=0)
    assert len(progressbar) == 2
    progressbar.update(2)
    our_file.seek(0)
    assert '| 2/2' in our_file.read()
    progressbar.desc = 'dynamically notify of 4 increments in total'
    progressbar.total = 4
    progressbar.update(-10)  # should default to +1
    our_file.seek(0)
    assert '| 3/4 ' in our_file.read()
    our_file.seek(0)
    assert 'dynamically notify of 4 increments in total' in our_file.read()
    our_file.close()


def test_close():
    """ Test manual creation and closure """
    # With `leave` option
    our_file = StringIO()
    progressbar = tqdm(total=3, file=our_file, miniters=10, leave=True)
    progressbar.update(3)
    our_file.seek(0)
    assert '| 3/3 ' not in our_file.read()  # Should be blank
    progressbar.close()
    our_file.seek(0)
    assert '| 3/3 ' in our_file.read()
    our_file.close()

    # Without `leave` option
    our_file2 = StringIO()
    progressbar2 = tqdm(total=3, file=our_file2, miniters=10)
    progressbar2.update(3)
    progressbar2.close()
    our_file2.seek(0)
    assert '| 3/3 ' not in our_file2.read()  # Should be blank
    our_file2.close()

    # With all updates
    our_file3 = StringIO()
    progressbar = tqdm(total=3, file=our_file3, miniters=0, mininterval=0,
                       leave=True)
    progressbar.update(3)
    our_file3.seek(0)
    out3 = our_file3.read()
    assert '| 3/3 ' in out3  # Should be blank
    progressbar.close()
    our_file3.seek(0)
    assert out3 + '\n' == our_file3.read()
    our_file3.close()


def test_smoothing():
    """ Test exponential weighted average smoothing """
    # -- Test disabling smoothing
    our_file = StringIO()
    for i in tqdm(_range(3), file=our_file, smoothing=None, leave=True):
        pass
    our_file.seek(0)
    assert '| 3/3 ' in our_file.read()
    our_file.close()

    # -- Test smoothing
    # Compile the regex to find the rate
    iterpattern = re.compile(r'(\d+\.\d+)it/s')
    # 1st case: no smoothing (only use average)
    our_file = StringIO()
    our_file2 = StringIO()
    t = tqdm(_range(3), file=our_file2, smoothing=None, leave=True, miniters=1,
             mininterval=0)
    for i in tqdm(_range(3), file=our_file, smoothing=None, leave=True,
                  miniters=1, mininterval=0):
        # Sleep more for first iteration and see how quickly rate is updated
        if i == 0:
            sleep(0.01)
        else:
            # Need to sleep in all iterations to calculate smoothed rate
            # (else delta_t is 0!)
            sleep(0.001)
        t.update()
    # Get result for iter-based bar
    our_file.seek(0)
    res = our_file.read().strip('\r').split('\r')
    m = iterpattern.search(res[3])
    a = float(m.group(1))
    our_file.close()
    # Get result for manually updated bar
    our_file2.seek(0)
    res = our_file2.read().strip('\r').split('\r')
    m = iterpattern.search(res[3])
    a2 = float(m.group(1))
    our_file2.close()

    # 2nd case: use max smoothing (= instant rate)
    our_file = StringIO()
    our_file2 = StringIO()
    t = tqdm(_range(3), file=our_file2, smoothing=1, leave=True, miniters=1,
             mininterval=0)
    for i in tqdm(_range(3), file=our_file, smoothing=1, leave=True,
                  miniters=1, mininterval=0):
        if i == 0:
            sleep(0.01)
        else:
            sleep(0.001)
        t.update()
    # Get result for iter-based bar
    our_file.seek(0)
    res = our_file.read().strip('\r').split('\r')
    m = iterpattern.search(res[3])
    b = float(m.group(1))
    our_file.close()
    # Get result for manually updated bar
    our_file2.seek(0)
    res = our_file2.read().strip('\r').split('\r')
    m = iterpattern.search(res[3])
    b2 = float(m.group(1))
    our_file2.close()

    # 3rd case: use medium smoothing
    our_file = StringIO()
    our_file2 = StringIO()
    t = tqdm(_range(3), file=our_file2, smoothing=0.5, leave=True, miniters=1,
             mininterval=0)
    for i in tqdm(_range(3), file=our_file, smoothing=0.5, leave=True,
                  miniters=1, mininterval=0):
        if i == 0:
            sleep(0.01)
        else:
            sleep(0.001)
        t.update()
    # Get result for iter-based bar
    our_file.seek(0)
    res = our_file.read().strip('\r').split('\r')
    m = iterpattern.search(res[3])
    c = float(m.group(1))
    our_file.close()
    # Get result for manually updated bar
    our_file2.seek(0)
    res = our_file2.read().strip('\r').split('\r')
    m = iterpattern.search(res[3])
    c2 = float(m.group(1))
    our_file2.close()

    # Check that medium smoothing's rate is between no and max smoothing rates
    assert a < c < b
    assert a2 < c2 < b2


def test_no_gui():
    """ Test internal GUI properties """
    # Check: StatusPrinter iff gui is disabled
    our_file = StringIO()
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
        for i in tqdm(_range(3), gui=True, file=our_file,
                      miniters=1, mininterval=0):
            pass
    except DeprecationWarning:
        pass
    else:
        raise DeprecationWarning('Should not allow manual gui=True without'
                                 ' overriding __iter__() and update()')

    t = tqdm(total=1, gui=False, file=our_file)
    assert hasattr(t, "sp")
    our_file.close()
