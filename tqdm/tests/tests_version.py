def test_version():
    from tqdm import __version__
    assert 3 <= len(__version__.split('.')) <= 4
