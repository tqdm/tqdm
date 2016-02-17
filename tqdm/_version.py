# Definition of the version number
version_info = 4, 1, 0  # major, minor, patch, -extra

# Nice string for the version
__version__ = '.'.join(map(str, version_info)).replace('.-', '-').strip('.-')
