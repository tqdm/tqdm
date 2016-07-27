from nose.plugins.skip import SkipTest

from tqdm import tqdm
from tests_tqdm import with_setup, pretest, posttest, StringIO, closing


@with_setup(pretest, posttest)
def test_pandas_groupby_apply():
    """ Test pandas.DataFrame.groupby(...).progress_apply """
    try:
        from numpy.random import randint
        import pandas as pd
    except:
        raise SkipTest

    with closing(StringIO()) as our_file:
        tqdm.pandas(file=our_file, leave=False, ascii=True)

        df = pd.DataFrame(randint(0, 50, (500, 3)))
        df.groupby(0).progress_apply(lambda x: None)

        dfs = pd.DataFrame(randint(0, 50, (500, 3)),
                           columns=list('abc'))
        dfs.groupby(['a']).progress_apply(lambda x: None)

        our_file.seek(0)

        # don't expect final output since no `leave` and
        # high dynamic `miniters`
        nexres = '100%|##########|'
        if nexres in our_file.read():
            our_file.seek(0)
            raise AssertionError("\nDid not expect:\n{0}\nIn:{1}\n".format(
                nexres, our_file.read()))


@with_setup(pretest, posttest)
def test_pandas_apply():
    """ Test pandas.DataFrame[.series].progress_apply """
    try:
        from numpy.random import randint
        import pandas as pd
    except:
        raise SkipTest

    with closing(StringIO()) as our_file:
        tqdm.pandas(file=our_file, leave=True, ascii=True)
        df = pd.DataFrame(randint(0, 50, (500, 3)))
        df.progress_apply(lambda x: None)

        dfs = pd.DataFrame(randint(0, 50, (500, 3)),
                           columns=list('abc'))
        dfs.a.progress_apply(lambda x: None)

        our_file.seek(0)

        if our_file.read().count('100%') < 2:
            our_file.seek(0)
            raise AssertionError("\nExpected:\n{0}\nIn:{1}\n".format(
                '100% at least twice', our_file.read()))


@with_setup(pretest, posttest)
def test_pandas_map():
    """ Test pandas.Series.progress_map """
    try:
        from numpy.random import randint
        import pandas as pd
    except:
        raise SkipTest

    with closing(StringIO()) as our_file:
        tqdm.pandas(file=our_file, leave=True, ascii=True)
        dfs = pd.DataFrame(randint(0, 50, (500, 3)),
                           columns=list('abc'))
        dfs.a.progress_map(lambda x: None)

        if our_file.getvalue().count('100%') < 1:
            raise AssertionError("\nExpected:\n{0}\nIn:{1}\n".format(
                '100% at least twice', our_file.getvalue()))


@with_setup(pretest, posttest)
def test_pandas_leave():
    """ Test pandas with `leave=True` """
    try:
        from numpy.random import randint
        import pandas as pd
    except:
        raise SkipTest

    with closing(StringIO()) as our_file:
        df = pd.DataFrame(randint(0, 100, (1000, 6)))
        tqdm.pandas(file=our_file, leave=True, ascii=True)
        df.groupby(0).progress_apply(lambda x: None)

        our_file.seek(0)

        exres = '100%|##########| 101/101'
        if exres not in our_file.read():
            our_file.seek(0)
            raise AssertionError("\nExpected:\n{0}\nIn:{1}\n".format(
                exres, our_file.read()))


@with_setup(pretest, posttest)
def test_pandas_deprecation():
    """ Test bar object instance as argument deprecation """
    try:
        from numpy.random import randint
        from tqdm import tqdm_pandas
        import pandas as pd
    except:
        raise SkipTest

    with closing(StringIO()) as our_file:
        tqdm_pandas(tqdm(file=our_file, leave=False, ascii=True, ncols=20))
        df = pd.DataFrame(randint(0, 50, (500, 3)))
        df.groupby(0).progress_apply(lambda x: None)
        # Check deprecation message
        assert "TqdmDeprecationWarning" in our_file.getvalue()
        assert "instead of `tqdm_pandas(tqdm(...))`" in our_file.getvalue()

    with closing(StringIO()) as our_file:
        tqdm_pandas(tqdm, file=our_file, leave=False, ascii=True, ncols=20)
        df = pd.DataFrame(randint(0, 50, (500, 3)))
        df.groupby(0).progress_apply(lambda x: None)
        # Check deprecation message
        assert "TqdmDeprecationWarning" in our_file.getvalue()
        assert "instead of `tqdm_pandas(tqdm, ...)`" in our_file.getvalue()
