from pytest import importorskip, mark

from tqdm import tqdm, tqdm_pandas

pytestmark = mark.slow

np = importorskip('numpy')
random = importorskip('numpy.random')
rand = random.rand
randint = random.randint
pd = importorskip('pandas')


def test_pandas_setup(caperr):
    tqdm.pandas(leave=True, ascii=True, total=123)
    series = pd.Series(randint(0, 50, (100,)))
    series.progress_apply(lambda x: x + 10)
    assert '100/123' in caperr()


def test_pandas_rolling_expanding(caperr):
    """Test pandas.{Series,DataFrame}.{rolling,expanding}"""
    tqdm.pandas(leave=True, ascii=True)

    series = pd.Series(randint(0, 50, (123,)))
    res1 = series.rolling(10).progress_apply(lambda x: 1, raw=True)
    res2 = series.rolling(10).apply(lambda x: 1, raw=True)
    assert res1.equals(res2)

    res3 = series.expanding(10).progress_apply(lambda x: 2, raw=True)
    res4 = series.expanding(10).apply(lambda x: 2, raw=True)
    assert res3.equals(res4)

    assert caperr().count('114it') >= 2  # 123-10+1


def test_pandas_series(caperr):
    """Test pandas.Series.progress_{apply,map}"""
    tqdm.pandas(leave=True, ascii=True)

    series = pd.Series(randint(0, 50, (123,)))
    res1 = series.progress_apply(lambda x: x + 10)
    res2 = series.apply(lambda x: x + 10)
    assert res1.equals(res2)

    res3 = series.progress_map(lambda x: x + 10)
    res4 = series.map(lambda x: x + 10)
    assert res3.equals(res4)

    err = caperr()
    assert err.count('100%') >= 2 and err.count('123/123') >= 2


@mark.filterwarnings("ignore:DataFrame.applymap has been deprecated:FutureWarning")
def test_pandas_data_frame(caperr):
    """Test pandas.DataFrame.progress_apply{,map}"""
    tqdm.pandas(leave=True, ascii=True)
    df = pd.DataFrame(randint(0, 50, (100, 200)))

    def task_func(x):
        return x + 1

    if hasattr(df, 'map'):  # pandas>=2.1.0
        # map
        res1 = df.progress_map(task_func)
        res2 = df.map(task_func)
        assert res1.equals(res2)
        expected = '200/200'
    else:
        # applymap
        res1 = df.progress_applymap(task_func)
        res2 = df.applymap(task_func)
        assert res1.equals(res2)
        expected = '20000/20000'
    assert expected in caperr()

    # apply unhashable
    res1 = []
    df.progress_apply(res1.extend)
    assert len(res1) == df.size

    # apply
    for axis in [0, 1, 'index', 'columns']:
        res3 = df.progress_apply(task_func, axis=axis)
        res4 = df.apply(task_func, axis=axis)
        assert res3.equals(res4)

    err = caperr()
    assert '200/200' in err  # axis=0
    assert '100/100' in err  # axis=1
    assert err.count('100%') >= 5


@mark.filterwarnings("ignore:DataFrameGroupBy.apply operated on the grouping columns")
def test_pandas_groupby_apply(caperr):
    """Test pandas.DataFrame.groupby(...).progress_apply"""
    tqdm.pandas(leave=False, ascii=True)

    df = pd.DataFrame(randint(0, 50, (500, 3)))
    df.groupby(0).progress_apply(lambda x: None)

    dfs = pd.DataFrame(randint(0, 50, (500, 3)), columns=list('abc'))
    dfs.groupby(['a']).progress_apply(lambda x: None)

    df2 = df = pd.DataFrame({'a': randint(1, 8, 10000), 'b': rand(10000)})
    res1 = df2.groupby("a").apply(np.maximum.reduce)
    res2 = df2.groupby("a").progress_apply(np.maximum.reduce)
    assert res1.equals(res2)

    # don't expect final output since no `leave` and high dynamic `miniters`
    assert '100%|##########|' not in caperr()

    tqdm.pandas(leave=True, ascii=True)

    dfs = pd.DataFrame(randint(0, 50, (500, 3)), columns=list('abc'))
    dfs.loc[0] = [2, 1, 1]
    dfs['d'] = 100

    dfs.groupby(dfs.index).progress_apply(lambda x: None)
    dfs.groupby('d').progress_apply(lambda x: None)
    dfs.T.groupby(dfs.columns).progress_apply(lambda x: None)
    dfs.T.groupby([2, 2, 1, 1]).progress_apply(lambda x: None)

    err = caperr()
    assert err.count('100%') >= 4
    assert all(exres in err for exres in ('500/500', '1/1', '4/4'))


@mark.filterwarnings("ignore:DataFrameGroupBy.apply operated on the grouping columns")
def test_pandas_leave(caperr):
    df = pd.DataFrame(randint(0, 100, (1000, 6)))
    tqdm.pandas(leave=True, ascii=True)
    df.groupby(0).progress_apply(lambda x: None)
    assert '100%|##########| 100/100' in caperr()


def test_pandas_apply_args_deprecation(caperr):
    """Test warning info in
    `pandas.Dataframe(Series).progress_apply(func, *args)`"""
    tqdm_pandas(tqdm(leave=False, ascii=True, ncols=20))
    df = pd.DataFrame(randint(0, 50, (500, 3)))
    df.progress_apply(lambda x: None, 1)  # 1 shall cause a warning
    # Check deprecation message
    err = caperr()
    assert all(i in err for i in (
        "TqdmDeprecationWarning", "not supported", "keyword arguments instead"))


@mark.filterwarnings("ignore:DataFrameGroupBy.apply operated on the grouping columns")
def test_pandas_deprecation(caperr):
    """Test bar object instance as argument deprecation"""
    df = pd.DataFrame(randint(0, 50, (500, 3)))

    tqdm_pandas(tqdm(leave=False, ascii=True, ncols=20))
    df.groupby(0).progress_apply(lambda x: None)
    err = caperr()
    assert "TqdmDeprecationWarning" in err
    assert "instead of `tqdm_pandas(tqdm(...))`" in err

    tqdm_pandas(tqdm, leave=False, ascii=True, ncols=20)
    df.groupby(0).progress_apply(lambda x: None)
    err = caperr()
    assert "TqdmDeprecationWarning" in err
    assert "instead of `tqdm_pandas(tqdm, ...)`" in err
