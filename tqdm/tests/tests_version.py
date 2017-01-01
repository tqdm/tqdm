import re


def test_version():
    """ Test version string """
    from tqdm import __version__
    version_parts = __version__.split()[0]  # remove part after space (branch name)
    version_parts = re.split('[.-]', version_parts)  # split by dot and dash
    assert 3 <= len(version_parts) <= 4
    try:
        map(int, version_parts[:3])
    except:
        raise TypeError('Version major, minor, patch must be integers')
