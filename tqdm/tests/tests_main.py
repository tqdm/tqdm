import sys
import subprocess
from os import path
from shutil import rmtree
from tempfile import mkdtemp
from tqdm import main, TqdmKeyError, TqdmTypeError

from tests_tqdm import with_setup, pretest, posttest, _range, closing, \
    UnicodeIO, StringIO


def _sh(*cmd, **kwargs):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            **kwargs).communicate()[0].decode('utf-8')


# WARNING: this should be the last test as it messes with sys.stdin, argv
@with_setup(pretest, posttest)
def test_main():
    """Test command line pipes"""
    ls_out = _sh('ls').replace('\r\n', '\n')
    ls = subprocess.Popen('ls', stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    res = _sh(sys.executable, '-c', 'from tqdm import main; main()',
              stdin=ls.stdout, stderr=subprocess.STDOUT)
    ls.wait()

    # actual test:

    assert ls_out in res.replace('\r\n', '\n')

    # semi-fake test which gets coverage:
    _SYS = sys.stdin, sys.argv

    with closing(StringIO()) as sys.stdin:
        sys.argv = ['', '--desc', 'Test CLI-delims',
                    '--ascii', 'True', '--delim', r'\0', '--buf_size', '64']
        sys.stdin.write('\0'.join(map(str, _range(int(1e3)))))
        sys.stdin.seek(0)
        main()

    IN_DATA_LIST = map(str, _range(int(1e3)))
    sys.stdin = IN_DATA_LIST
    sys.argv = ['', '--desc', 'Test CLI pipes',
                '--ascii', 'True', '--unit_scale', 'True']
    import tqdm.__main__  # NOQA

    IN_DATA = '\0'.join(IN_DATA_LIST)
    with closing(StringIO()) as sys.stdin:
        sys.stdin.write(IN_DATA)
        sys.stdin.seek(0)
        sys.argv = ['', '--ascii', '--bytes', '--unit_scale', 'False']
        with closing(UnicodeIO()) as fp:
            main(fp=fp)
            assert str(len(IN_DATA)) in fp.getvalue()

    sys.stdin = IN_DATA_LIST
    sys.argv = ['', '-ascii', '--unit_scale', 'False',
                '--desc', 'Test CLI errors']
    main()

    sys.argv = ['', '-ascii', '-unit_scale', '--bad_arg_u_ment', 'foo']
    try:
        main()
    except TqdmKeyError as e:
        if 'bad_arg_u_ment' not in str(e):
            raise
    else:
        raise TqdmKeyError('bad_arg_u_ment')

    sys.argv = ['', '-ascii', '-unit_scale', 'invalid_bool_value']
    try:
        main()
    except TqdmTypeError as e:
        if 'invalid_bool_value' not in str(e):
            raise
    else:
        raise TqdmTypeError('invalid_bool_value')

    sys.argv = ['', '-ascii', '--total', 'invalid_int_value']
    try:
        main()
    except TqdmTypeError as e:
        if 'invalid_int_value' not in str(e):
            raise
    else:
        raise TqdmTypeError('invalid_int_value')

    # test SystemExits
    for i in ('-h', '--help', '-v', '--version'):
        sys.argv = ['', i]
        try:
            main()
        except SystemExit:
            pass

    # test --manpath
    tmp = mkdtemp()
    man = path.join(tmp, "tqdm.1")
    assert not path.exists(man)
    try:
        main(argv=['--manpath', tmp])
    except SystemExit:
        pass
    else:
        raise SystemExit("Expected system exit")
    assert path.exists(man)
    rmtree(tmp, True)

    # test --log
    with closing(StringIO()) as sys.stdin:
        sys.stdin.write('\0'.join(map(str, _range(int(1e3)))))
        sys.stdin.seek(0)
        # with closing(UnicodeIO()) as fp:
        main(argv=['--log', 'DEBUG'])
        # assert "DEBUG:" in sys.stdout.getvalue()

    # clean up
    sys.stdin, sys.argv = _SYS
