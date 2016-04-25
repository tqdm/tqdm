import sys
import subprocess
from tqdm import main
from copy import deepcopy

from tests_tqdm import with_setup, pretest, posttest, _range


def _sh(*cmd, **kwargs):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            **kwargs).communicate()[0].decode('utf-8')


# WARNING: this should be the last test as it messes with sys.stdin, argv
@with_setup(pretest, posttest)
def test_main():
    """ Test command line pipes """
    ls_out = _sh('ls').replace('\r\n', '\n')
    ls = subprocess.Popen(('ls'), stdout=subprocess.PIPE)
    res = _sh('python', '-c', 'from tqdm import main; main()',
              stdin=ls.stdout, stderr=subprocess.STDOUT)
    ls.wait()

    # actual test:

    assert (ls_out in res.replace('\r\n', '\n'))

    # semi-fake test which gets coverage:
    try:
        _SYS = (deepcopy(sys.stdin), deepcopy(sys.argv))
    except:
        pass

    sys.stdin = map(str, _range(int(1e3)))
    sys.argv = ['', '--desc', 'Test CLI pipes',
                '--ascii', 'True', '--unit_scale', 'True']
    import tqdm.__main__  # NOQA

    sys.argv = ['', '--ascii', '--unit_scale', 'False',
                '--desc', 'Test CLI errors']
    main()

    sys.argv = ['', '--bad_arg_u_ment', 'foo', '--ascii', '--unit_scale']
    try:
        main()
    except KeyError as e:
        if 'bad_arg_u_ment' not in str(e):
            raise

    sys.argv = ['', '--ascii', '--unit_scale', 'invalid_bool_value']
    try:
        main()
    except ValueError as e:
        if 'invalid_bool_value' not in str(e):
            raise

    sys.argv = ['', '--ascii', '--total', 'invalid_int_value']
    try:
        main()
    except ValueError as e:
        if 'invalid_int_value' not in str(e):
            raise

    for i in ('-h', '--help', '-v', '--version'):
        sys.argv = ['', i]
        try:
            main()
        except SystemExit:
            pass

    # clean up
    try:
        sys.stdin, sys.argv = _SYS
    except:
        pass
