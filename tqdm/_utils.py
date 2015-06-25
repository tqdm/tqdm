try:    # pragma: no cover
    _range = xrange
except NameError:    # pragma: no cover
    _range = range


try:    # pragma: no cover
    _unich = unichr
except NameError:    # pragma: no cover
    _unich = chr


def _is_utf(encoding):
    return ('U8' == encoding) or ('utf' in encoding) or ('UTF' in encoding)


def _supports_unicode(file):
    if not getattr(file, 'encoding', None):
        return False
    return _is_utf(file.encoding)


def _environ_cols(file):  # pragma: no cover
    try:
        from termios import TIOCGWINSZ
        from fcntl import ioctl
        from array import array
    except ImportError:
        return None
    else:
        try:
            return array('h', ioctl(file, TIOCGWINSZ, '\0' * 8))[1]
        except:
            try:
                from os.environ import get
            except ImportError:
                return None
            else:
                return int(get('COLUMNS', 1)) - 1
