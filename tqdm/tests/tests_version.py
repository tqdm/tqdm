import re


def test_version():
    """ Test version string """
    from tqdm import __version__
    Mmpe = __version__.split()[0]  # remove part after space (branch name)
    Mmpe = re.split('[.-]', Mmpe)  # split by dot and dash
    assert 3 <= len(Mmpe) <= 4
    try:
        map(int, Mmpe[:3])
    except:
        raise TypeError('Version major, minor, patch must be integers')
