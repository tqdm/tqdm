from __future__ import unicode_literals
from tqdm import format_interval, format_meter


def test_format_interval():
    assert format_interval(60) == '01:00'
    assert format_interval(6160) == '1:42:40'
    assert format_interval(238113) == '66:08:33'


def test_format_meter():
    assert format_meter(231, 1000, 392) == \
        "|##--------| 231/1000  23% [elapsed: " \
        "06:32 left: 12:49,  0.00 iters/sec]"

