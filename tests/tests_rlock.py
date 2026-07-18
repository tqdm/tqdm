from .tests_tqdm import StringIO, closing, importorskip, mark, skip


@mark.slow
def test_rlock_creation():
    """Test that importing tqdm does not create multiprocessing objects."""
    mp = importorskip('multiprocessing')
    if not hasattr(mp, 'get_context'):
        skip("missing multiprocessing.get_context")

    # Use 'spawn' instead of 'fork' so that the process does not inherit any
    # globals that have been constructed by running other tests
    ctx = mp.get_context('spawn')
    with ctx.Pool(1) as pool:
        # The pool will propagate the error if the target method fails
        pool.apply(_rlock_creation_target)


def _rlock_creation_target():
    """Check that the RLock has not been constructed."""
    import multiprocessing as mp
    patch = importorskip('unittest.mock').patch

    # Patch the RLock class/method but use the original implementation
    with patch('multiprocessing.RLock', wraps=mp.RLock) as rlock_mock:
        # Importing the module should not create a lock
        from tqdm import tqdm
        assert rlock_mock.call_count == 0
        # Creating a progress bar should initialize the lock
        with closing(StringIO()) as our_file:
            with tqdm(file=our_file) as _:  # NOQA
                pass
        assert rlock_mock.call_count == 1
        # Creating a progress bar again should reuse the lock
        with closing(StringIO()) as our_file:
            with tqdm(file=our_file) as _:  # NOQA
                pass
        assert rlock_mock.call_count == 1
