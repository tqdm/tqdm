from tests_tqdm import posttest, pretest, with_setup

from tqdm.notebook import tqdm as tqdm_notebook


@with_setup(pretest, posttest)
def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")
