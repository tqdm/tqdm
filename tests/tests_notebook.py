from tqdm.notebook import tqdm as tqdm_notebook
from .tests_tqdm import pretest_posttest  # NOQA, pylint: disable=unused-import


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")
