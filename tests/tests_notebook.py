from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_update_returns_none():
    """Test that tqdm_notebook.update() returns None to avoid Jupyter auto-display"""
    with tqdm_notebook(total=10, disable=True) as t:
        result = t.update(1)
        assert result is None
