from nose.plugins.skip import SkipTest

from tqdm import tqdm
from tests_tqdm import with_setup, pretest, posttest, StringIO, closing


@with_setup(pretest, posttest)
def test_pandas():
    try:
        from numpy.random import randint
        from tqdm import tqdm_pandas
        import pandas as pd
    except:
        raise SkipTest

    with closing(StringIO()) as our_file:
        df = pd.DataFrame(randint(0, 100, (1000, 6)))
        tqdm_pandas(tqdm(file=our_file, leave=False, ascii=True))
        df.groupby(0).progress_apply(lambda x: None)

        our_file.seek(0)

        try:
            # don't expect final output since no `leave` and
            # high dynamic `miniters`
            assert '100%|##########| 101/101' not in our_file.read()
        except:
            raise AssertionError('Did not expect:\n\t100%|##########| 101/101')


@with_setup(pretest, posttest)
def test_pandas_leave():
    try:
        from numpy.random import randint
        from tqdm import tqdm_pandas
        import pandas as pd
    except:
        raise SkipTest

    with closing(StringIO()) as our_file:
        df = pd.DataFrame(randint(0, 100, (1000, 6)))
        tqdm_pandas(tqdm(file=our_file, leave=True, ascii=True))
        df.groupby(0).progress_apply(lambda x: None)

        our_file.seek(0)

        try:
            assert '100%|##########| 101/101' in our_file.read()
        except:
            our_file.seek(0)
            raise AssertionError('\n'.join(('Expected:',
                                            '100%|##########| 101/101', 'Got:',
                                            our_file.read())))
