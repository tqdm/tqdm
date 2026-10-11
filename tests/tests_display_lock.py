"""Display methods must release the global lock when output fails."""
import errno
from io import StringIO
from threading import Thread
from unittest.mock import Mock

from pytest import mark, raises

from tqdm import tqdm


class FailingIO(StringIO):
    error = OSError()
    operation = None
    failing = False

    def write(self, value):
        if self.operation == 'write' and self.failing:
            raise self.error
        return super().write(value)

    def flush(self):
        if self.operation == 'flush' and self.failing:
            raise self.error
        return super().flush()


def lock_available(lock):
    """Probe from another thread: the owning thread could reacquire an RLock."""
    result = []

    def probe():
        acquired = lock.acquire(False)
        result.append(acquired)
        if acquired:
            lock.release()

    thread = Thread(target=probe)
    thread.start()
    thread.join(timeout=5)
    assert not thread.is_alive()
    return result[0]


@mark.parametrize('method, mode', [
    ('clear', 'default'), ('clear', 'nolock'),
    ('refresh', 'default'), ('refresh', 'nolock'), ('refresh', 'lock_args')])
@mark.parametrize('operation', ['write', 'flush'])
def test_display_error_releases_lock(thread_lock, method, operation, mode):
    with FailingIO() as file, tqdm(file=file) as bar:
        error = OSError(errno.ENOSPC, 'output failed')
        file.error, file.operation, file.failing = error, operation, True
        nolock = mode == 'nolock'
        kwargs = {'nolock': nolock}
        if mode == 'lock_args' and method == 'refresh':
            kwargs['lock_args'] = (False,)
        if nolock:
            thread_lock.acquire()
        try:
            with raises(OSError) as caught:
                getattr(bar, method)(**kwargs)
            assert caught.value is error
            assert not bar.disable
            assert lock_available(thread_lock) is (not nolock)
        finally:
            file.failing = False
            # Drain any leaked acquisitions even on the unfixed implementation,
            # so a failing regression cannot deadlock later tests or the monitor.
            while True:
                try:
                    thread_lock.release()
                except RuntimeError:
                    break
        assert lock_available(thread_lock)


@mark.parametrize('method', ['clear', 'refresh'])
@mark.parametrize('operation', ['write', 'flush'])
def test_display_suppressed_error(thread_lock, method, operation):
    with FailingIO() as file, tqdm(file=file) as bar:
        file.error = OSError(errno.EIO, 'output failed')
        file.operation, file.failing = operation, True
        try:
            getattr(bar, method)()
            assert bar.miniters == float('inf')
            assert not bar.disable
            assert lock_available(thread_lock)
        finally:
            file.failing = False


@mark.parametrize('method', ['clear', 'refresh'])
@mark.parametrize('nolock', [False, True])
def test_display_lock_success(thread_lock, tmp_file, monkeypatch, method, nolock):
    with tqdm(file=tmp_file, bar_format='{n}') as bar, monkeypatch.context() as patch:
        patch.setattr(bar, '_lock', Mock(wraps=thread_lock))
        tmp_file.seek(0)
        tmp_file.truncate()
        result = getattr(bar, method)(nolock=nolock)
        assert result is (True if method == 'refresh' else None)
        assert tmp_file.getvalue() == ('\r0' if method == 'refresh' else '\r \r')
        assert bar._lock.acquire.call_count == (0 if nolock else 1)
        assert bar._lock.release.call_count == (0 if nolock else 1)
        assert lock_available(thread_lock)


@mark.parametrize('acquired', [False, True])
def test_refresh_lock_args(thread_lock, tmp_file, monkeypatch, acquired):
    with tqdm(file=tmp_file) as bar, monkeypatch.context() as patch:
        patch.setattr(bar, '_lock', Mock(wraps=thread_lock))
        if not acquired:
            bar._lock.acquire.return_value = False
        bar.display = Mock()
        assert bar.refresh(lock_args=(False,)) is acquired
        bar._lock.acquire.assert_called_once_with(False)
        assert bar._lock.release.call_count == int(acquired)
        assert bar.display.call_count == int(acquired)
        assert lock_available(thread_lock)


@mark.parametrize('method', ['clear', 'refresh'])
def test_display_disabled_does_not_lock(tmp_file, method):
    with tqdm(file=tmp_file, disable=True) as bar:
        bar._lock = Mock()
        assert getattr(bar, method)() is None
        bar._lock.acquire.assert_not_called()
        bar._lock.release.assert_not_called()
        assert not tmp_file.getvalue()
