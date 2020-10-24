"""Test CLI usage."""
from io import open as io_open
from os import path
from shutil import rmtree
from tempfile import mkdtemp
import sys
import subprocess

from tqdm.cli import main, TqdmKeyError, TqdmTypeError
from tqdm.utils import IS_WIN
from .tests_tqdm import pretest_posttest  # NOQA, pylint: disable=unused-import
from .tests_tqdm import skip, _range, closing, UnicodeIO, StringIO, BytesIO


def _sh(*cmd, **kwargs):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            **kwargs).communicate()[0].decode('utf-8')


class Null(object):
    def __call__(self, *_, **__):
        return self

    def __getattr__(self, _):
        return self


NULL = Null()


def test_pipes():
    """Test command line pipes"""
    ls_out = _sh('ls').replace('\r\n', '\n')
    ls = subprocess.Popen('ls', stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    res = _sh(sys.executable, '-c', 'from tqdm.cli import main; main()',
              stdin=ls.stdout, stderr=subprocess.STDOUT)
    ls.wait()

    # actual test:

    assert ls_out in res.replace('\r\n', '\n')


# WARNING: this should be the last test as it messes with sys.stdin, argv
def test_main():
    """Test misc CLI options"""
    _SYS = sys.stdin, sys.argv
    _STDOUT = sys.stdout
    N = 123

    # test direct import
    sys.stdin = [str(i).encode() for i in _range(N)]
    sys.argv = ['', '--desc', 'Test CLI import',
                '--ascii', 'True', '--unit_scale', 'True']
    import tqdm.__main__  # NOQA
    sys.stderr.write("Test misc CLI options ... ")

    # test --delim
    IN_DATA = '\0'.join(map(str, _range(N))).encode()
    with closing(BytesIO()) as sys.stdin:
        sys.argv = ['', '--desc', 'Test CLI delim',
                    '--ascii', 'True', '--delim', r'\0', '--buf_size', '64']
        sys.stdin.write(IN_DATA)
        # sys.stdin.write(b'\xff')  # TODO
        sys.stdin.seek(0)
        with closing(UnicodeIO()) as fp:
            main(fp=fp)
            assert str(N) + "it" in fp.getvalue()

    # test --bytes
    IN_DATA = IN_DATA.replace(b'\0', b'\n')
    with closing(BytesIO()) as sys.stdin:
        sys.stdin.write(IN_DATA)
        sys.stdin.seek(0)
        sys.argv = ['', '--ascii', '--bytes=True', '--unit_scale', 'False']
        with closing(UnicodeIO()) as fp:
            main(fp=fp)
            assert str(len(IN_DATA)) in fp.getvalue()

    # test --log
    sys.stdin = [str(i).encode() for i in _range(N)]
    # with closing(UnicodeIO()) as fp:
    main(argv=['--log', 'DEBUG'], fp=NULL)
    # assert "DEBUG:" in sys.stdout.getvalue()

    try:
        # test --tee
        IN_DATA = IN_DATA.decode()
        with closing(StringIO()) as sys.stdout:
            with closing(StringIO()) as sys.stdin:
                sys.stdin.write(IN_DATA)

                sys.stdin.seek(0)
                with closing(UnicodeIO()) as fp:
                    main(argv=['--mininterval', '0', '--miniters', '1'], fp=fp)
                    res = len(fp.getvalue())
                    # assert len(fp.getvalue()) < len(sys.stdout.getvalue())

                sys.stdin.seek(0)
                with closing(UnicodeIO()) as fp:
                    main(argv=['--tee', '--mininterval', '0',
                               '--miniters', '1'], fp=fp)
                    # spaces to clear intermediate lines could increase length
                    assert len(fp.getvalue()) >= res + len(IN_DATA)

        # test --null
        with closing(StringIO()) as sys.stdout:
            with closing(StringIO()) as sys.stdin:
                sys.stdin.write(IN_DATA)

                sys.stdin.seek(0)
                with closing(UnicodeIO()) as fp:
                    main(argv=['--null'], fp=fp)
                    assert not sys.stdout.getvalue()

            with closing(StringIO()) as sys.stdin:
                sys.stdin.write(IN_DATA)

                sys.stdin.seek(0)
                with closing(UnicodeIO()) as fp:
                    main(argv=[], fp=fp)
                    assert sys.stdout.getvalue()
    finally:
        sys.stdout = _STDOUT

    # test integer --update
    IN_DATA = IN_DATA.encode()
    with closing(BytesIO()) as sys.stdin:
        sys.stdin.write(IN_DATA)

        sys.stdin.seek(0)
        with closing(UnicodeIO()) as fp:
            main(argv=['--update'], fp=fp)
            res = fp.getvalue()
            assert str(N // 2 * N) + "it" in res  # arithmetic sum formula

    # test integer --update --delim
    with closing(BytesIO()) as sys.stdin:
        sys.stdin.write(IN_DATA.replace(b'\n', b'D'))

        sys.stdin.seek(0)
        with closing(UnicodeIO()) as fp:
            main(argv=['--update', '--delim', 'D'], fp=fp)
            res = fp.getvalue()
            assert str(N // 2 * N) + "it" in res  # arithmetic sum formula

    # test integer --update_to
    with closing(BytesIO()) as sys.stdin:
        sys.stdin.write(IN_DATA)

        sys.stdin.seek(0)
        with closing(UnicodeIO()) as fp:
            main(argv=['--update-to'], fp=fp)
            res = fp.getvalue()
            assert str(N - 1) + "it" in res
            assert str(N) + "it" not in res

    # test integer --update_to --delim
    with closing(BytesIO()) as sys.stdin:
        sys.stdin.write(IN_DATA.replace(b'\n', b'D'))

        sys.stdin.seek(0)
        with closing(UnicodeIO()) as fp:
            main(argv=['--update-to', '--delim', 'D'], fp=fp)
            res = fp.getvalue()
            assert str(N - 1) + "it" in res
            assert str(N) + "it" not in res

    # test float --update_to
    IN_DATA = '\n'.join((str(i / 2.0) for i in _range(N))).encode()
    with closing(BytesIO()) as sys.stdin:
        sys.stdin.write(IN_DATA)

        sys.stdin.seek(0)
        with closing(UnicodeIO()) as fp:
            main(argv=['--update-to'], fp=fp)
            res = fp.getvalue()
            assert str((N - 1) / 2.0) + "it" in res
            assert str(N / 2.0) + "it" not in res

    # clean up
    sys.stdin, sys.argv = _SYS


def test_manpath():
    """Test CLI --manpath"""
    if IS_WIN:
        skip("no manpages on windows")
    tmp = mkdtemp()
    man = path.join(tmp, "tqdm.1")
    assert not path.exists(man)
    try:
        main(argv=['--manpath', tmp], fp=NULL)
    except SystemExit:
        pass
    else:
        raise SystemExit("Expected system exit")
    assert path.exists(man)
    rmtree(tmp, True)


def test_comppath():
    """Test CLI --comppath"""
    if IS_WIN:
        skip("no manpages on windows")
    tmp = mkdtemp()
    man = path.join(tmp, "tqdm_completion.sh")
    assert not path.exists(man)
    try:
        main(argv=['--comppath', tmp], fp=NULL)
    except SystemExit:
        pass
    else:
        raise SystemExit("Expected system exit")
    assert path.exists(man)

    # check most important options appear
    with io_open(man, mode='r', encoding='utf-8') as fd:
        script = fd.read()
    opts = set([
        '--help', '--desc', '--total', '--leave', '--ncols', '--ascii',
        '--dynamic_ncols', '--position', '--bytes', '--nrows', '--delim',
        '--manpath', '--comppath'
    ])
    assert all(args in script for args in opts)
    rmtree(tmp, True)


def test_exceptions():
    """Test CLI Exceptions"""
    _SYS = sys.stdin, sys.argv
    sys.stdin = map(str, _range(123))

    sys.argv = ['', '-ascii', '-unit_scale', '--bad_arg_u_ment', 'foo']
    try:
        main(fp=NULL)
    except TqdmKeyError as e:
        if 'bad_arg_u_ment' not in str(e):
            raise
    else:
        raise TqdmKeyError('bad_arg_u_ment')

    sys.argv = ['', '-ascii', '-unit_scale', 'invalid_bool_value']
    try:
        main(fp=NULL)
    except TqdmTypeError as e:
        if 'invalid_bool_value' not in str(e):
            raise
    else:
        raise TqdmTypeError('invalid_bool_value')

    sys.argv = ['', '-ascii', '--total', 'invalid_int_value']
    try:
        main(fp=NULL)
    except TqdmTypeError as e:
        if 'invalid_int_value' not in str(e):
            raise
    else:
        raise TqdmTypeError('invalid_int_value')

    sys.argv = ['', '--update', '--update_to']
    try:
        main(fp=NULL)
    except TqdmKeyError as e:
        if 'Can only have one of --' not in str(e):
            raise
    else:
        raise TqdmKeyError('Cannot have both --update --update_to')

    # test SystemExits
    for i in ('-h', '--help', '-v', '--version'):
        sys.argv = ['', i]
        try:
            main(fp=NULL)
        except SystemExit:
            pass
        else:
            raise ValueError('expected SystemExit')

    # clean up
    sys.stdin, sys.argv = _SYS
