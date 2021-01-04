"""Test CLI usage."""
from os import linesep
import logging
import sys
import subprocess

from pytest import mark, raises

from tqdm.cli import main, TqdmKeyError, TqdmTypeError
from tqdm.utils import IS_WIN
from .tests_tqdm import _range, closing, BytesIO


def norm(bytestr):
    """Normalise line endings."""
    return bytestr if linesep == "\n" else bytestr.replace(linesep.encode(), b"\n")


def test_pipes():
    """Test command line pipes"""
    ls_out = subprocess.check_output(['ls'])
    ls = subprocess.Popen(['ls'], stdout=subprocess.PIPE)
    res = subprocess.Popen(
        [sys.executable, '-c', 'from tqdm.cli import main; main()'],
        stdin=ls.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = res.communicate()
    assert ls.poll() == 0

    # actual test:
    assert norm(ls_out) == norm(out)
    assert b"it/s" in err


if sys.version_info[:2] >= (3, 8):
    test_pipes = mark.filterwarnings("ignore:unclosed file:ResourceWarning")(
        test_pipes)


def test_main_import():
    """Test main CLI import"""
    _SYS = sys.stdin, sys.argv
    N = 123

    # test direct import
    sys.stdin = [str(i).encode() for i in _range(N)]
    sys.argv = ['', '--desc', 'Test CLI import',
                '--ascii', 'True', '--unit_scale', 'True']
    import tqdm.__main__  # NOQA

    sys.stdin, sys.argv = _SYS


def test_main_bytes(capsysbinary):
    """Test CLI --bytes"""
    _SYS = sys.stdin
    N = 123

    # test --delim
    IN_DATA = '\0'.join(map(str, _range(N))).encode()
    with closing(BytesIO()) as sys.stdin:
        sys.stdin.write(IN_DATA)
        # sys.stdin.write(b'\xff')  # TODO
        sys.stdin.seek(0)
        main(sys.stderr, ['--desc', 'Test CLI delim', '--ascii', 'True',
                          '--delim', r'\0', '--buf_size', '64'])
        out, err = capsysbinary.readouterr()
        assert out == IN_DATA
        assert str(N) + "it" in err.decode("U8")

    # test --bytes
    IN_DATA = IN_DATA.replace(b'\0', b'\n')
    with closing(BytesIO()) as sys.stdin:
        sys.stdin.write(IN_DATA)
        sys.stdin.seek(0)
        main(sys.stderr, ['--ascii', '--bytes=True', '--unit_scale', 'False'])
        out, err = capsysbinary.readouterr()
        assert out == IN_DATA
        assert str(len(IN_DATA)) + "B" in err.decode("U8")

    sys.stdin = _SYS


def test_main(capsysbinary, caplog):
    """Test misc CLI options"""
    _SYS = sys.stdin
    N = 123
    sys.stdin = [(str(i) + '\n').encode() for i in _range(N)]
    IN_DATA = b''.join(sys.stdin)

    # test --log
    with caplog.at_level(logging.INFO):
        main(sys.stderr, ['--log', 'INFO'])
        out, err = capsysbinary.readouterr()
        assert norm(out) == IN_DATA and b"123/123" in err
        assert not caplog.record_tuples
    with caplog.at_level(logging.DEBUG):
        main(sys.stderr, ['--log', 'DEBUG'])
        out, err = capsysbinary.readouterr()
        assert norm(out) == IN_DATA and b"123/123" in err
        assert caplog.record_tuples

    # test --tee
    main(sys.stderr, ['--mininterval', '0', '--miniters', '1'])
    out, err = capsysbinary.readouterr()
    assert norm(out) == IN_DATA and b"123/123" in err
    assert N <= len(err.split(b"\r")) < N + 5

    len_err = len(err)
    main(sys.stderr, ['--tee', '--mininterval', '0', '--miniters', '1'])
    out, err = capsysbinary.readouterr()
    assert norm(out) == IN_DATA and b"123/123" in err
    # spaces to clear intermediate lines could increase length
    assert len_err + len(norm(out)) <= len(err)

    # test --null
    main(sys.stderr, ['--null'])
    out, err = capsysbinary.readouterr()
    assert not out and b"123/123" in err

    # test integer --update
    main(sys.stderr, ['--update'])
    out, err = capsysbinary.readouterr()
    assert norm(out) == IN_DATA
    assert (str(N // 2 * N) + "it").encode() in err, "expected arithmetic sum formula"

    # test integer --update_to
    main(sys.stderr, ['--update-to'])
    out, err = capsysbinary.readouterr()
    assert norm(out) == IN_DATA
    assert (str(N - 1) + "it").encode() in err
    assert (str(N) + "it").encode() not in err

    with closing(BytesIO()) as sys.stdin:
        sys.stdin.write(IN_DATA.replace(b'\n', b'D'))

        # test integer --update --delim
        sys.stdin.seek(0)
        main(sys.stderr, ['--update', '--delim', 'D'])
        out, err = capsysbinary.readouterr()
        assert out == IN_DATA.replace(b'\n', b'D')
        assert (str(N // 2 * N) + "it").encode() in err, "expected arithmetic sum"

        # test integer --update_to --delim
        sys.stdin.seek(0)
        main(sys.stderr, ['--update-to', '--delim', 'D'])
        out, err = capsysbinary.readouterr()
        assert out == IN_DATA.replace(b'\n', b'D')
        assert (str(N - 1) + "it").encode() in err
        assert (str(N) + "it").encode() not in err

    # test float --update_to
    sys.stdin = [(str(i / 2.0) + '\n').encode() for i in _range(N)]
    IN_DATA = b''.join(sys.stdin)
    main(sys.stderr, ['--update-to'])
    out, err = capsysbinary.readouterr()
    assert norm(out) == IN_DATA
    assert (str((N - 1) / 2.0) + "it").encode() in err
    assert (str(N / 2.0) + "it").encode() not in err

    # clean up
    sys.stdin = _SYS


@mark.skipif(IS_WIN, reason="no manpages on windows")
def test_manpath(tmp_path):
    """Test CLI --manpath"""
    man = tmp_path / "tqdm.1"
    assert not man.exists()
    with raises(SystemExit):
        main(argv=['--manpath', str(tmp_path)])
    assert man.is_file()


@mark.skipif(IS_WIN, reason="no completion on windows")
def test_comppath(tmp_path):
    """Test CLI --comppath"""
    man = tmp_path / "tqdm_completion.sh"
    assert not man.exists()
    with raises(SystemExit):
        main(argv=['--comppath', str(tmp_path)])
    assert man.is_file()

    # check most important options appear
    script = man.read_text()
    opts = {'--help', '--desc', '--total', '--leave', '--ncols', '--ascii',
            '--dynamic_ncols', '--position', '--bytes', '--nrows', '--delim',
            '--manpath', '--comppath'}
    assert all(args in script for args in opts)


def test_exceptions(capsysbinary):
    """Test CLI Exceptions"""
    _SYS = sys.stdin
    N = 123
    sys.stdin = [str(i) + '\n' for i in _range(N)]
    IN_DATA = ''.join(sys.stdin).encode()

    with raises(TqdmKeyError, match="bad_arg_u_ment"):
        main(sys.stderr, argv=['-ascii', '-unit_scale', '--bad_arg_u_ment', 'foo'])
    out, _ = capsysbinary.readouterr()
    assert norm(out) == IN_DATA

    with raises(TqdmTypeError, match="invalid_bool_value"):
        main(sys.stderr, argv=['-ascii', '-unit_scale', 'invalid_bool_value'])
    out, _ = capsysbinary.readouterr()
    assert norm(out) == IN_DATA

    with raises(TqdmTypeError, match="invalid_int_value"):
        main(sys.stderr, argv=['-ascii', '--total', 'invalid_int_value'])
    out, _ = capsysbinary.readouterr()
    assert norm(out) == IN_DATA

    with raises(TqdmKeyError, match="Can only have one of --"):
        main(sys.stderr, argv=['--update', '--update_to'])
    out, _ = capsysbinary.readouterr()
    assert norm(out) == IN_DATA

    # test SystemExits
    for i in ('-h', '--help', '-v', '--version'):
        with raises(SystemExit):
            main(argv=[i])

    # clean up
    sys.stdin = _SYS
