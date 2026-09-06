import logging
import subprocess  # nosec
import sys
from io import BytesIO
from os import linesep

from pytest import mark, raises

from tqdm.cli import TqdmKeyError, TqdmTypeError, main
from tqdm.utils import IS_WIN


def norm(bytestr):
    """Normalise line endings."""
    return bytestr if linesep == "\n" else bytestr.replace(linesep.encode(), b"\n")


@mark.slow
@mark.filterwarnings("ignore:unclosed file:ResourceWarning")
def test_pipes():
    ls_out = subprocess.check_output(['ls'])  # nosec
    ls = subprocess.Popen(['ls'], stdout=subprocess.PIPE)  # nosec
    res = subprocess.Popen(  # nosec
        [sys.executable, '-c', 'from tqdm.cli import main; main()'],
        stdin=ls.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = res.communicate()
    assert ls.poll() == 0

    # actual test:
    assert norm(ls_out) == norm(out)
    assert b"it/s" in err
    assert b"Error" not in err


def test_main_import(monkeypatch):
    N = 123
    monkeypatch.setattr(sys, 'stdin', [str(i).encode() for i in range(N)])
    monkeypatch.setattr(sys, 'argv', ['', '--desc', 'Test CLI import',
                                      '--ascii', 'True', '--unit_scale', 'True'])
    import tqdm.__main__  # noqa: F401, pylint: disable=unused-import


def test_main_bytes(capsysbinary, monkeypatch):
    N = 123

    # test --delim
    IN_DATA = '\0'.join(map(str, range(N))).encode()
    monkeypatch.setattr(sys, 'stdin', BytesIO())
    sys.stdin.write(IN_DATA)
    # sys.stdin.write(b'\xff')  # TODO
    sys.stdin.seek(0)
    main(sys.stderr, ['--desc', 'Test CLI delim', '--ascii', 'True',
                      '--delim', r'\0', '--buf_size', '64'])
    out, err = capsysbinary.readouterr()
    assert out == IN_DATA
    assert str(N) + "it" in err.decode('U8')

    # test --bytes
    IN_DATA = IN_DATA.replace(b'\0', b'\n')
    monkeypatch.setattr(sys, 'stdin', BytesIO(IN_DATA))
    main(sys.stderr, ['--ascii', '--bytes=True', '--unit_scale', 'False'])
    out, err = capsysbinary.readouterr()
    assert out == IN_DATA
    assert str(len(IN_DATA)) + "B" in err.decode('U8')


@mark.parametrize("level,logged", [("INFO", False), ("DEBUG", True)])
def test_main_log(capsysbinary, caplog, monkeypatch, level, logged):
    N = 123
    lines = [(str(i) + '\n').encode() for i in range(N)]
    monkeypatch.setattr(sys, 'stdin', lines)
    with caplog.at_level(getattr(logging, level)):
        main(sys.stderr, ['--log', level])
        out, err = capsysbinary.readouterr()
        assert norm(out) == b''.join(lines) and b"123/123" in err
        assert bool(caplog.record_tuples) is logged


def test_main_misc_options(capsysbinary, monkeypatch):
    N = 123
    monkeypatch.setattr(sys, 'stdin', [(str(i) + '\n').encode() for i in range(N)])
    IN_DATA = b''.join(sys.stdin)

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

    DELIM_DATA = IN_DATA.replace(b'\n', b'D')

    # test integer --update --delim
    monkeypatch.setattr(sys, 'stdin', BytesIO(DELIM_DATA))
    main(sys.stderr, ['--update', '--delim', 'D'])
    out, err = capsysbinary.readouterr()
    assert out == DELIM_DATA
    assert (str(N // 2 * N) + "it").encode() in err, "expected arithmetic sum"

    # test integer --update_to --delim
    monkeypatch.setattr(sys, 'stdin', BytesIO(DELIM_DATA))
    main(sys.stderr, ['--update-to', '--delim', 'D'])
    out, err = capsysbinary.readouterr()
    assert out == DELIM_DATA
    assert (str(N - 1) + "it").encode() in err
    assert (str(N) + "it").encode() not in err

    # test float --update_to
    monkeypatch.setattr(sys, 'stdin', [(str(i / 2.0) + '\n').encode() for i in range(N)])
    IN_DATA = b''.join(sys.stdin)
    main(sys.stderr, ['--update-to'])
    out, err = capsysbinary.readouterr()
    assert norm(out) == IN_DATA
    assert (str((N - 1) / 2.0) + "it").encode() in err
    assert (str(N / 2.0) + "it").encode() not in err


@mark.slow
@mark.skipif(IS_WIN, reason="no man pages on windows")
def test_manpath(tmp_path):
    man = tmp_path / "tqdm.1"
    assert not man.exists()
    with raises(SystemExit):
        main(argv=['--manpath', str(tmp_path)])
    assert man.is_file()


@mark.slow
@mark.skipif(IS_WIN, reason="no completion on windows")
def test_comppath(tmp_path):
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


def test_exceptions(capsysbinary, monkeypatch):
    N = 123
    monkeypatch.setattr(sys, 'stdin', [str(i) + '\n' for i in range(N)])
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
