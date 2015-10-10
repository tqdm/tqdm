from __future__ import unicode_literals

import csv

try:
    from StringIO import StringIO
except:
    from io import StringIO

from tqdm import format_interval
from tqdm import format_meter
from tqdm import tqdm
from tqdm import trange


def test_format_interval():
    assert format_interval(60) == '01:00'
    assert format_interval(6160) == '1:42:40'
    assert format_interval(238113) == '66:08:33'


def test_format_meter():
    try:
        unich = unichr
    except NameError:
        unich = chr

    assert format_meter(0, 1000, 13) == \
        "  0%|          | 0/1000 [00:13<?,  0.00it/s]"
    assert format_meter(0, 1000, 13, ncols=68, prefix='desc: ') == \
        "desc:   0%|                            | 0/1000 [00:13<?,  0.00it/s]"
    assert format_meter(231, 1000, 392) == \
        " 23%|" + unich(0x2588)*2 + unich(0x258e) + \
        "       | 231/1000 [06:32<21:44,  0.59it/s]"
    assert format_meter(10000, 1000, 13) == \
        "10000it [00:13, 769.23it/s]"
    assert format_meter(231, 1000, 392, ncols=56, ascii=True) == \
        " 23%|" + '#'*3 + '6' + \
        "            | 231/1000 [06:32<21:44,  0.59it/s]"
    assert format_meter(100000, 1000, 13, unit_scale=True, unit='iB') == \
        "100KiB [00:13, 7.69KiB/s]"
    assert format_meter(100, 1000, 12, ncols=0) == \
        " 10% 100/1000 [00:12<01:48,  8.33it/s]"


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
    progressbar = tqdm(range(10))
    assert len(progressbar) == 10
    for i in progressbar:
        pass
    import sys
    sys.stderr.write('tests_tqdm.test_all_defaults ... ')


def test_iterate_over_csv_rows():
    # Create a test csv pseudo file
    test_csv_file = StringIO()
    writer = csv.writer(test_csv_file)
    for i in range(3):
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
    for i in tqdm(range(3), file=our_file):
        if i == 1:
            our_file.seek(0)
            assert '0/3' in our_file.read()


def test_leave_option():
    """ Test `leave=True` always prints info about the last iteration. """
    our_file = StringIO()
    for i in tqdm(range(3), file=our_file, leave=True):
        pass
    our_file.seek(0)
    assert '| 3/3 ' in our_file.read()
    our_file.seek(0)
    assert '\n' == our_file.read()[-1]  # not '\r'
    our_file.close()

    our_file2 = StringIO()
    for i in tqdm(range(3), file=our_file2, leave=False):
        pass
    our_file2.seek(0)
    assert '| 3/3 ' not in our_file2.read()
    our_file2.close()


def test_trange():
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
    our_file = StringIO()
    for i in tqdm(range(3), file=our_file, mininterval=1e-10):
        pass
    our_file.seek(0)
    assert "  0%|          | 0/3 [00:00<" in our_file.read()
    our_file.close()


def test_min_iters():
    our_file = StringIO()
    for i in tqdm(range(3), file=our_file, leave=True, miniters=4):
        our_file.write('blank\n')
    our_file.seek(0)
    assert '\nblank\nblank\n' in our_file.read()
    our_file.close()

    our_file2 = StringIO()
    for i in tqdm(range(3), file=our_file2, leave=True, miniters=1):
        our_file2.write('blank\n')
    our_file2.seek(0)
    # assume automatic mininterval = 0 means intermediate output
    assert '| 3/3 ' in our_file2.read()
    our_file2.close()


def test_disable():
    our_file = StringIO()
    for i in tqdm(range(3), file=our_file, disable=True):
        pass
    our_file.seek(0)
    assert our_file.read() == ""

    our_file2 = StringIO()
    progressbar = tqdm(total=3, file=our_file2, miniters=1, disable=True)
    progressbar.update(3)
    progressbar.close()
    our_file2.seek(0)
    assert our_file2.read() == ""


def test_unit():
    our_file = StringIO()
    for i in tqdm(range(3), file=our_file, miniters=1, unit="bytes"):
        pass
    our_file.seek(0)
    assert "bytes/s" in our_file.read()
    our_file.close()


def test_update():
    """ Test manual creation and updates """
    our_file = StringIO()
    progressbar = tqdm(total=2, file=our_file, miniters=1)
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
