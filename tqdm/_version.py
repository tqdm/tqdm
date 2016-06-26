# Definition of the version number
try:
    from ._utils import _sh
except:  # pragma: no cover
    _sh = None

from subprocess import STDOUT
__all__ = ["__version__"]

# major, minor, patch, -extra
version_info = 4, 7, 6

# Nice string for the version
__version__ = '.'.join(map(str, version_info))


# auto -extra based on commit hash (if not tagged as release)
if (_sh is not None) and (len(version_info) < 4):  # pragma: no cover
    def commit_hash(*args):
        try:
            res = _sh('git', 'log', '-n', '1', '--oneline', *args,
                      stderr=STDOUT).lstrip().split()[0]
            return None if res.startswith('fatal') else res
        except:
            return None

    cur_hash = commit_hash()
    if cur_hash is not None:
        last_release = commit_hash('v' + __version__)

        if (last_release is None) or (cur_hash not in last_release):
            __version__ += '-' + cur_hash
