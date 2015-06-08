from __future__ import unicode_literals

try:
    from StringIO import StringIO
except:
    from io import StringIO

import time

from nose.plugins.skip import SkipTest
from nose.tools import with_setup

from tqdm import tqdm

def setup_pandas():
    try:
        from tqdm import enable_progress_apply
        enable_progress_apply()
    except:
        raise SkipTest


@with_setup(setup_pandas)
def test_pandas():

    import pandas as pd
    import numpy as np

    our_file = StringIO()

    df = pd.DataFrame(np.random.randint(0, 100, (1000, 6)))
    df.groupby(0).progress_apply(lambda x: time.sleep(0.01),
                                 progress_kwargs=dict(file=our_file, leave=False))

    our_file.seek(0)

    assert "|##########| 100/100 100%" in our_file.read()


@with_setup(setup_pandas)
def test_pandas_leave():

    import pandas as pd
    import numpy as np

    our_file = StringIO()

    df = pd.DataFrame(np.random.randint(0, 100, (1000, 6)))
    df.groupby(0).progress_apply(lambda x: time.sleep(0.01),
                                 progress_kwargs=dict(file=our_file, leave=True))
    our_file.seek(0)

    assert "|##########| 100/100 100%" in our_file.read()
