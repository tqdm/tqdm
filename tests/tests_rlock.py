from io import StringIO
from unittest.mock import Mock

from pytest import importorskip, mark, raises


@mark.parametrize("args", [(), (False,), (True,)])
def test_default_lock_acquire(args):
    from tqdm.std import TqdmDefaultWriteLock

    lock = TqdmDefaultWriteLock()
    acquired = lock.acquire(*args)
    lock.release()
    assert acquired is True


@mark.parametrize("position", [0, 1, 2])
@mark.parametrize("failure", [False, RuntimeError("acquire failed"), KeyboardInterrupt()])
def test_default_lock_acquire_failure(position, failure):
    from tqdm.std import TqdmDefaultWriteLock

    lock = TqdmDefaultWriteLock()
    lock.locks = [Mock() for _ in range(3)]
    released = []
    for index, child in enumerate(lock.locks):
        child.acquire.return_value = True
        child.release.side_effect = lambda index=index: released.append(index)
    lock.locks[position].acquire.side_effect = [failure]

    if failure is False:
        assert lock.acquire(False) is False
    else:
        with raises(type(failure)) as exc:
            lock.acquire(False)
        assert exc.value is failure

    assert released == list(range(position))[::-1]
    for index, child in enumerate(lock.locks):
        assert child.acquire.call_count == (index <= position)
        assert child.release.call_count == (index < position)


@mark.slow
def test_rlock_creation():
    """Test that importing tqdm does not create multiprocessing objects."""
    mp = importorskip('multiprocessing')
    # Use 'spawn' instead of 'fork' so that the process does not inherit any
    # globals that have been constructed by running other tests
    ctx = mp.get_context('spawn')
    with ctx.Pool(1) as pool:
        # The pool will propagate the error if the target method fails
        pool.apply(_rlock_creation_target)


def _rlock_creation_target():
    """Check that the RLock has not been constructed."""
    import multiprocessing as mp
    from unittest.mock import patch

    # Patch the RLock class/method but use the original implementation
    with patch('multiprocessing.RLock', wraps=mp.RLock) as rlock_mock:
        # Importing the module should not create a lock
        from tqdm import tqdm
        assert rlock_mock.call_count == 0
        # Creating a progress bar should initialize the lock
        with StringIO() as tmp_file:
            with tqdm(file=tmp_file) as _:  # NOQA
                pass
        assert rlock_mock.call_count == 1
        # Creating a progress bar again should reuse the lock
        with StringIO() as tmp_file:
            with tqdm(file=tmp_file) as _:  # NOQA
                pass
        assert rlock_mock.call_count == 1
