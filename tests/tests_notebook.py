from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_disabled_display():
    """Test that display() does not raise for disabled tqdm_notebook"""
    with tqdm_notebook(total=10, desc="Processing tasks", disable=True) as t:
        t.display()
        t.refresh()
