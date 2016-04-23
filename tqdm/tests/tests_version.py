import re


def test_version():
    """ Test version string """
    from tqdm import __version__
    Mmpe = re.split('[.-]', __version__)
    assert 3 <= len(Mmpe) <= 4
    try:
        map(int, Mmpe[:3])
    except:
        raise TypeError('Version major, minor, patch must be integers')
