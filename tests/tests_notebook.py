from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_leave_false_closes_incomplete_bar():
    """Test that leave=False hides a manually closed incomplete bar"""
    t = tqdm_notebook(range(3), leave=False, display=False)
    for _ in t:
        t.close()
        break

    assert t.container.children[1].bar_style != 'danger'
    assert t.container.layout.visibility == 'hidden'
