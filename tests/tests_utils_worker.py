"""Tests for the latest-waiting-task policy in MonoWorker."""
from threading import Event

from pytest import mark

from tqdm.contrib.utils_worker import MonoWorker


@mark.parametrize('in_callback', [False, True])
def test_submit_replaces_waiting_task(in_callback):
    worker = MonoWorker()
    release_task = Event()
    callback_started = Event()
    release_callback = Event()
    calls = []

    def first_task():
        assert release_task.wait(5)
        calls.append('first')

    def block_callback(_):
        callback_started.set()
        assert release_callback.wait(5)

    try:
        first = worker.submit(first_task)
        first.add_done_callback(block_callback)
        stale = worker.submit(calls.append, 'stale')
        if in_callback:
            # The future is done, but the worker cannot start the queued task.
            release_task.set()
            assert callback_started.wait(5)

        latest = worker.submit(calls.append, 'latest')
        assert stale.cancelled()
        release_task.set()
        release_callback.set()
        latest.result(timeout=5)
        assert calls == ['first', 'latest']
    finally:
        release_task.set()
        release_callback.set()
        worker.pool.shutdown(wait=True)


def test_submit_keeps_new_running_task():
    worker = MonoWorker()
    started = Event()
    release = Event()
    calls = []

    def running_task():
        started.set()
        assert release.wait(5)
        calls.append('running')

    try:
        worker.submit(lambda: None).result(timeout=5)
        running = worker.submit(running_task)
        assert started.wait(5)
        stale = worker.submit(calls.append, 'stale')
        latest = worker.submit(calls.append, 'latest')
        assert not running.cancelled()
        assert stale.cancelled()
        release.set()
        latest.result(timeout=5)
        assert calls == ['running', 'latest']
    finally:
        release.set()
        worker.pool.shutdown(wait=True)
