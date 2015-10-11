def test_version():
    from tqdm import __version__
    assert len(__version__.split('.')) == 4
