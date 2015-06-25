def _is_utf(encoding):
    return ('U8' == encoding) or ('utf' in encoding) or ('UTF' in encoding)


def _supports_unicode(file):
    if not getattr(file, 'encoding', None):
        return False
    return _is_utf(file.encoding)


def _environ_cols():  # pragma: no cover
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
                from os import environ
            except ImportError:
                return None
            else:
                return int(environ.get('COLUMNS', 1)) - 1
