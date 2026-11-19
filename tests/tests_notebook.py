from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_ncols_uses_character_units():
    """Numeric ncols is measured in characters, while CSS widths are preserved."""
    container = tqdm_notebook.status_printer(None, total=1, ncols=79)
    assert container.layout.width == "79ch"

    for ncols in ("79px", "100%"):
        container = tqdm_notebook.status_printer(None, total=1, ncols=ncols)
        assert container.layout.width == ncols
