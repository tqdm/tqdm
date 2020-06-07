from tqdm.notebook import tqdm as tqdm_notebook
from tests_tqdm import with_setup, pretest, posttest


@with_setup(pretest, posttest)
def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")
