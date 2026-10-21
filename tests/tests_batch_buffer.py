"""
Unit and regression tests for BatchBuffer core utility in tqdm.

Tests all code paths, branches, and edge cases for `BatchBuffer` and `tqdm.buffered()`:
- `__init__`: parameter validation (type, range, thread_safe flag)
- `push(n)`: chunk flushing, remainder retention, thread-safe vs unlocked
- `__call__(n)`: callable interface equivalence to push
- `flush()`: remainder transfer and idempotency (buffer == 0 vs buffer != 0)
- `close()`: flushing on detachment
- Context managers: sync `__enter__`/`__exit__` and async `__aenter__`/`__aexit__`
- Concurrency: multi-threaded safety with `threading.Lock`
- Boundary cases: `batch_size=1`, large batch size, zero and negative pushes
"""

import io
import threading

import pytest
from pytest import raises

from tqdm import BatchBuffer, tqdm


def test_batch_size_validation_invalid_types():
    """Verify non-integer/unconvertible types raise ValueError."""
    s = io.StringIO()
    with tqdm(total=10, file=s) as pbar:
        with raises(ValueError, match="batch_size must be an integer >= 1"):
            BatchBuffer(pbar, batch_size="invalid")

        with raises(ValueError, match="batch_size must be an integer >= 1"):
            BatchBuffer(pbar, batch_size=None)

        with raises(ValueError, match="batch_size must be an integer >= 1"):
            BatchBuffer(pbar, batch_size=[10])


def test_batch_size_validation_less_than_one():
    """Verify batch_size < 1 raises ValueError."""
    s = io.StringIO()
    with tqdm(total=10, file=s) as pbar:
        with raises(ValueError, match="batch_size must be >= 1"):
            BatchBuffer(pbar, batch_size=0)

        with raises(ValueError, match="batch_size must be >= 1"):
            BatchBuffer(pbar, batch_size=-5)


def test_batch_size_valid_conversions():
    """Verify float and string integers convert cleanly to int."""
    s = io.StringIO()
    with tqdm(total=10, file=s) as pbar:
        buf1 = BatchBuffer(pbar, batch_size=50.0)
        assert buf1.batch_size == 50

        buf2 = BatchBuffer(pbar, batch_size="250")
        assert buf2.batch_size == 250


def test_push_accumulation_and_chunk_flushing_unlocked():
    """Verify push accumulation and exact chunk flushes without lock."""
    s = io.StringIO()
    with tqdm(total=500, file=s) as pbar:
        buf = BatchBuffer(pbar, batch_size=100, thread_safe=False)
        assert buf._lock is None

        # Pushing less than batch_size does not update pbar
        buf.push(50)
        assert pbar.n == 0
        assert buf._buffer == 50

        # Pushing remainder to reach capacity flushes exact chunk
        buf.push(50)
        assert pbar.n == 100
        assert buf._buffer == 0

        # Pushing multiple chunks at once flushes multiples and leaves remainder
        buf.push(250)
        assert pbar.n == 300
        assert buf._buffer == 50

        buf.flush()
        assert pbar.n == 350
        assert buf._buffer == 0


def test_push_accumulation_and_chunk_flushing_locked():
    """Verify push accumulation and exact chunk flushes with thread_safe=True."""
    s = io.StringIO()
    with tqdm(total=500, file=s) as pbar:
        buf = BatchBuffer(pbar, batch_size=100, thread_safe=True)
        assert buf._lock is not None

        buf.push(60)
        assert pbar.n == 0
        assert buf._buffer == 60

        buf.push(40)
        assert pbar.n == 100
        assert buf._buffer == 0

        buf.push(230)
        assert pbar.n == 300
        assert buf._buffer == 30

        buf.flush()
        assert pbar.n == 330
        assert buf._buffer == 0


def test_callable_interface():
    """Verify buffer instance callable signature buf(n) and buf()."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        buf = BatchBuffer(pbar, batch_size=10)

        # Default argument n=1
        buf()
        assert buf._buffer == 1

        # Explicit n argument
        buf(9)
        assert pbar.n == 10
        assert buf._buffer == 0

        buf(5)
        buf.flush()
        assert pbar.n == 15


def test_flush_remainder_and_idempotency_unlocked():
    """Verify flush handles uncommitted remainder and is idempotent when empty."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        buf = BatchBuffer(pbar, batch_size=50, thread_safe=False)
        buf.push(20)
        assert pbar.n == 0

        # First flush updates pbar
        buf.flush()
        assert pbar.n == 20
        assert buf._buffer == 0

        # Second flush when buffer is 0 does not update pbar again
        buf.flush()
        assert pbar.n == 20
        assert buf._buffer == 0


def test_flush_remainder_and_idempotency_locked():
    """Verify flush handles uncommitted remainder and is idempotent with lock."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        buf = BatchBuffer(pbar, batch_size=50, thread_safe=True)
        buf.push(35)
        assert pbar.n == 0

        buf.flush()
        assert pbar.n == 35
        assert buf._buffer == 0

        buf.flush()
        assert pbar.n == 35
        assert buf._buffer == 0


def test_close_flushes_pending_buffer():
    """Verify close() delegates to flush() to commit pending iterations."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        buf = BatchBuffer(pbar, batch_size=50)
        buf.push(18)
        assert pbar.n == 0

        buf.close()
        assert pbar.n == 18
        assert buf._buffer == 0


def test_context_manager_sync_normal_and_exception():
    """Verify sync context manager auto-flushes on normal and exceptional exit."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        with BatchBuffer(pbar, batch_size=50) as buf:
            buf.push(12)
        assert pbar.n == 12

    # Exception inside context
    with tqdm(total=100, file=s) as pbar2:
        with raises(ZeroDivisionError):
            with BatchBuffer(pbar2, batch_size=50) as buf2:
                buf2.push(27)
                _ = 1 / 0
        assert pbar2.n == 27


@pytest.mark.asyncio
async def test_context_manager_async_normal_and_exception():
    """Verify async context manager auto-flushes on normal and exceptional exit."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        async with BatchBuffer(pbar, batch_size=50) as buf:
            buf.push(14)
        assert pbar.n == 14

    # Exception inside async context
    with tqdm(total=100, file=s) as pbar2:
        with raises(KeyError):
            async with BatchBuffer(pbar2, batch_size=50) as buf2:
                buf2.push(33)
                raise KeyError("test error")
        assert pbar2.n == 33


def test_tqdm_buffered_factory_method():
    """Verify pbar.buffered() factory returns correctly initialized BatchBuffer."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        buf = pbar.buffered()
        assert isinstance(buf, BatchBuffer)
        assert buf.batch_size == 1000
        assert buf._lock is None

        buf_custom = pbar.buffered(batch_size=200, thread_safe=True)
        assert buf_custom.batch_size == 200
        assert buf_custom._lock is not None

        # Context manager usage via factory
        with pbar.buffered(batch_size=50) as b:
            b.push(45)
        assert pbar.n == 45


def test_tqdm_batch_buffer_attribute():
    """Verify tqdm.BatchBuffer is bound to the BatchBuffer class."""
    assert hasattr(tqdm, "BatchBuffer")
    assert tqdm.BatchBuffer is BatchBuffer


def test_multithreaded_concurrency_thread_safe():
    """Verify thread-safety when multiple worker threads push to shared buffer."""
    s = io.StringIO()
    num_threads = 10
    pushes_per_thread = 100
    expected_total = num_threads * pushes_per_thread

    with tqdm(total=expected_total, file=s) as pbar:
        with BatchBuffer(pbar, batch_size=25, thread_safe=True) as buf:
            def worker():
                for _ in range(pushes_per_thread):
                    buf.push(1)

            threads = [threading.Thread(target=worker) for _ in range(num_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

    assert pbar.n == expected_total


def test_push_zero_and_negative_adjustments():
    """Verify push(0) and negative push adjustments behave consistently."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        buf = BatchBuffer(pbar, batch_size=20)
        buf.push(0)
        assert buf._buffer == 0
        assert pbar.n == 0

        buf.push(15)
        buf.push(-5)
        assert buf._buffer == 10

        buf.flush()
        assert pbar.n == 10


def test_batch_size_one_flushes_immediately():
    """Verify batch_size=1 flushes immediately on every push."""
    s = io.StringIO()
    with tqdm(total=10, file=s) as pbar:
        with BatchBuffer(pbar, batch_size=1) as buf:
            buf.push(1)
            assert pbar.n == 1
            buf.push(2)
            assert pbar.n == 3
        assert pbar.n == 3


def test_large_batch_size_exceeding_total():
    """Verify batch_size exceeding total iterations buffers all and flushes on close."""
    s = io.StringIO()
    with tqdm(total=20, file=s) as pbar:
        with BatchBuffer(pbar, batch_size=5000) as buf:
            for _ in range(20):
                buf.push(1)
            assert pbar.n == 0
        assert pbar.n == 20
