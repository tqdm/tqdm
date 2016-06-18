import sys
import subprocess
from tqdm import main, TqdmKeyError, TqdmTypeError
import re
# from copy import deepcopy

from tests_tqdm import with_setup, pretest, posttest, _range
from tests_tqdm import StringIO as UnicodeIO


def _sh(*cmd, **kwargs):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            **kwargs).communicate()[0].decode('utf-8')


RE_TQDM_OUT = re.compile(r'[\r]\d+it \[\d\d:\d\d, (?:[\d.]+|\?)(?:it/s|s/it)\]')


# WARNING: this should be the last test as it messes with sys.stdin, argv
@with_setup(pretest, posttest)
def test_main():
    """ Test command line pipes """
    ls_out = _sh('dir')
    ls = subprocess.Popen(('dir'),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    res = _sh('python', '-c', r'import sys; sys.argv = ["", "--delim", "\\t"];'
                              ' from tqdm import main; main()',
              stdin=ls.stdout,
              stderr=subprocess.STDOUT)
    ls.wait()

    # actual test:
    res_split = RE_TQDM_OUT.split(res)
    assert res_split[-1][:2] == '\r\n'  # tqdm's extra newline
    res_stripped = ''.join(res_split[:-1]) + res_split[-1][2:]
    assert ls_out == res_stripped

    # semi-fake tests which get coverage:
    try:
        _SYS = sys.stdin, sys.argv  # map(deepcopy, (sys.stdin, sys.argv))
    except:
        pass

    sys.stdin = UnicodeIO()
    sys.argv = ['', '--desc', 'Test CLI delims',
                '--ascii', 'True', '--delim', r'\0', '--buf_size', '64']
    sys.stdin.write('\0'.join(map(str, _range(int(1e3)))))
    sys.stdin.seek(0)
    main()

    sys.stdin.seek(0)
    sys.stdin.write('\n'.join(map(str, _range(int(1e3)))))

    sys.stdin.seek(0)
    sys.argv = ['', '--desc', 'Test CLI pipes',
                '--ascii', 'True', '--unit_scale', 'True']
    import tqdm.__main__  # NOQA

    sys.argv = ['', '-ascii', '--unit_scale', 'False',
                '--desc', 'Test CLI errors']
    main()

    sys.stdin.seek(0)
    sys.argv = ['', '-ascii', '-unit_scale', '--bad_arg_u_ment', 'foo']
    try:
        main()
    except TqdmKeyError as e:
        if 'bad_arg_u_ment' not in str(e):
            raise
    else:
        raise TqdmKeyError('bad_arg_u_ment')

    sys.stdin.seek(0)
    sys.argv = ['', '-ascii', '-unit_scale', 'invalid_bool_value']
    try:
        main()
    except TqdmTypeError as e:
        if 'invalid_bool_value' not in str(e):
            raise
    else:
        raise TqdmTypeError('invalid_bool_value')

    sys.stdin.seek(0)
    sys.argv = ['', '-ascii', '--total', 'invalid_int_value']
    try:
        main()
    except TqdmTypeError as e:
        if 'invalid_int_value' not in str(e):
            raise
    else:
        raise TqdmTypeError('invalid_int_value')

    for i in ('-h', '--help', '-v', '--version'):
        sys.stdin.seek(0)
        sys.argv = ['', i]
        try:
            main()
        except SystemExit:
            pass

    # clean up
    sys.stdin.close()
    try:
        sys.stdin, sys.argv = _SYS
    except:
        pass
