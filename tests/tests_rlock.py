import os
import subprocess
import sys
from io import StringIO

from pytest import importorskip, mark


@mark.slow
def test_rlock_creation():
    """Test that importing tqdm does not create multiprocessing objects."""
    importorskip('multiprocessing')
    # Run the check in a new interpreter so that it does not inherit any
    # globals that have been constructed by running other tests.
    # A 'spawn' pool would also re-import the main module of this process,
    # which fails when pytest is started from a script without a
    # `if __name__ == '__main__'` guard (#1638).
    # Pass on the import path, as 'spawn' does, in case tqdm is not installed.
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
    subprocess.run([sys.executable, __file__], check=True, env=env)


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


if __name__ == '__main__':
    _rlock_creation_target()
