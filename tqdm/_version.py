# Definition of the version number
from ._utils import _sh
from subprocess import STDOUT
__all__ = ["__version__"]


def commit_hash(*args):
    try:
        return _sh('git', 'log', '-n', '1', '--oneline', *args,
                   stderr=STDOUT).lstrip().split()[0]
    except:
        return None


# major, minor, patch, -extra
version_info = 4, 4, 0

# Nice string for the version
__version__ = '.'.join(map(str, version_info))

cur_hash = commit_hash()
if cur_hash is not None:
    last_release = commit_hash('v' + __version__).rstrip(':').lower()

    if 'fatal' in last_release or cur_hash not in last_release:
        __version__ += '-' + cur_hash
