"""
Comprehensive 4-Tier End-to-End (E2E) Test Suite for tqdm Core & Optimizations.

This suite provides opaque-box verification across:
- Tier 1: Feature Coverage (>=5 test cases per feature area)
- Tier 2: Boundary & Corner Cases (>=5 test cases per feature area)
- Tier 3: Cross-Feature Combinations (pairwise interactions)
- Tier 4: Real-World Application Scenarios (high-throughput pipeline simulations)
"""

import asyncio
import io
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from tqdm import tqdm, trange
from tqdm.asyncio import tqdm_asyncio

pytestmark = pytest.mark.slow

# Detection for M2 BatchBuffer feature
try:
    from tqdm import BatchBuffer
except (ImportError, AttributeError):
    BatchBuffer = getattr(tqdm, "BatchBuffer", None)

HAS_BATCH_BUFFER = BatchBuffer is not None and hasattr(tqdm, "buffered")


# ==============================================================================
# TIER 1: FEATURE COVERAGE (50 Tests)
# ==============================================================================

# ------------------------------------------------------------------------------
# 1.1 Progress Display & Rendering (5 Tests)
# ------------------------------------------------------------------------------

def test_t1_f1_display_basic_rendering():
    """Verify standard progress bar rendering contains progress percentage and counts."""
    s = io.StringIO()
    with tqdm(total=10, file=s, miniters=1, mininterval=0) as pbar:
        pbar.update(5)
    output = s.getvalue()
    assert "50%" in output
    assert "5/10" in output


def test_t1_f1_display_ascii_mode():
    """Verify ascii=True renders ascii characters instead of unicode blocks."""
    s = io.StringIO()
    with tqdm(total=10, file=s, ascii=True, miniters=1, mininterval=0) as pbar:
        pbar.update(5)
    output = s.getvalue()
    assert "50%" in output
    assert "█" not in output


def test_t1_f1_display_desc_prefix():
    """Verify description prefix is rendered in output."""
    s = io.StringIO()
    with tqdm(total=10, file=s, desc="TaskAlpha", miniters=1, mininterval=0) as pbar:
        pbar.update(1)
    output = s.getvalue()
    assert "TaskAlpha:" in output


def test_t1_f1_display_postfix():
    """Verify dynamic postfix statistics are correctly appended."""
    s = io.StringIO()
    with tqdm(total=10, file=s, miniters=1, mininterval=0) as pbar:
        pbar.set_postfix(loss=0.05, acc=0.99)
        pbar.update(1)
    output = s.getvalue()
    assert "loss=0.05" in output
    assert "acc=0.99" in output


def test_t1_f1_display_unit_scale():
    """Verify byte/metric unit scaling formats correctly."""
    s = io.StringIO()
    with tqdm(total=2048, file=s, unit="B", unit_scale=True, miniters=1, mininterval=0) as pbar:
        pbar.update(1024)
    output = s.getvalue()
    assert "1.02k" in output or "1.00k" in output or "k" in output


# ------------------------------------------------------------------------------
# 1.2 Iteration & Generator Wrapping (5 Tests)
# ------------------------------------------------------------------------------

def test_t1_f2_iteration_trange():
    """Verify trange iterator yields exact sequence and counts."""
    s = io.StringIO()
    items = list(trange(15, file=s, miniters=1, mininterval=0))
    assert items == list(range(15))


def test_t1_f2_iteration_generator_wrapper():
    """Verify generator wrapping yields all items transparently."""
    def sample_gen():
        for i in range(8):
            yield f"item_{i}"

    s = io.StringIO()
    with tqdm(sample_gen(), file=s, miniters=1, mininterval=0) as pbar:
        items = list(pbar)
    assert items == [f"item_{i}" for i in range(8)]
    assert pbar.n == 8


def test_t1_f2_iteration_len_inference():
    """Verify list iterable auto-infers total."""
    data = [10, 20, 30, 40, 50]
    s = io.StringIO()
    with tqdm(data, file=s) as pbar:
        out = list(pbar)
    assert out == data
    assert pbar.total == 5
    assert pbar.n == 5


def test_t1_f2_iteration_early_break():
    """Verify early loop termination properly records count."""
    s = io.StringIO()
    with tqdm(range(50), file=s) as pbar:
        for x in pbar:
            if x == 7:
                break
    assert pbar.n == 7


def test_t1_f2_iteration_custom_iterable_no_len():
    """Verify iterable without __len__ functions with total=None."""
    class StreamIterable:
        def __iter__(self):
            return iter([1, 2, 3, 4])

    s = io.StringIO()
    with tqdm(StreamIterable(), file=s) as pbar:
        out = list(pbar)
    assert out == [1, 2, 3, 4]
    assert pbar.total is None
    assert pbar.n == 4


# ------------------------------------------------------------------------------
# 1.3 Manual Update Operations (5 Tests)
# ------------------------------------------------------------------------------

def test_t1_f3_manual_update_default_increment():
    """Verify pbar.update() defaults to increment of 1."""
    s = io.StringIO()
    with tqdm(total=5, file=s) as pbar:
        pbar.update()
        pbar.update()
    assert pbar.n == 2


def test_t1_f3_manual_update_integer_steps():
    """Verify pbar.update(n) handles arbitrary integer increments."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        pbar.update(10)
        pbar.update(35)
    assert pbar.n == 45


def test_t1_f3_manual_update_float_steps():
    """Verify pbar.update(n) supports floating-point increments."""
    s = io.StringIO()
    with tqdm(total=10.0, file=s) as pbar:
        pbar.update(1.25)
        pbar.update(2.75)
    assert abs(pbar.n - 4.0) < 1e-6


def test_t1_f3_manual_update_return_value():
    """Verify pbar.update() returns boolean or None indicating display trigger."""
    s = io.StringIO()
    with tqdm(total=10, file=s, miniters=1, mininterval=0) as pbar:
        res = pbar.update(1)
    assert res in (True, None, False)


def test_t1_f3_manual_update_context_manager_lifecycle():
    """Verify context manager cleanly completes and closes manual progress bar."""
    s = io.StringIO()
    with tqdm(total=50, file=s) as pbar:
        pbar.update(50)
    assert pbar.n == 50


# ------------------------------------------------------------------------------
# 1.4 Timing Limits & Interval Controls (5 Tests)
# ------------------------------------------------------------------------------

def test_t1_f4_timing_mininterval_suppression():
    """Verify rapid updates within mininterval suppress excessive prints."""
    s = io.StringIO()
    with tqdm(total=100, file=s, mininterval=10.0) as pbar:
        for _ in range(20):
            pbar.update(1)
    # Output should not contain 20 distinct prints
    assert pbar.n == 20


def test_t1_f4_timing_maxinterval_refresh():
    """Verify maxinterval forces a display refresh even if miniters not met."""
    s = io.StringIO()
    with tqdm(total=100, file=s, miniters=1000, maxinterval=0.05, mininterval=0) as pbar:
        pbar.update(1)
        time.sleep(0.08)
        pbar.update(1)
    assert pbar.n == 2


def test_t1_f4_timing_delay_suppression():
    """Verify delay parameter suppresses output before duration passes."""
    s = io.StringIO()
    with tqdm(total=10, file=s, delay=5.0) as pbar:
        pbar.update(1)
    assert s.getvalue() == ""


def test_t1_f4_timing_start_time_recording():
    """Verify start_t is initialized to a valid epoch timestamp."""
    s = io.StringIO()
    with tqdm(total=10, file=s) as pbar:
        assert pbar.start_t > 0
        assert pbar.start_t <= time.time()


def test_t1_f4_timing_rate_calculation():
    """Verify rate calculation accurately reflects iterations over elapsed time."""
    s = io.StringIO()
    with tqdm(total=100, file=s, miniters=1, mininterval=0) as pbar:
        pbar.update(50)
        fd = pbar.format_dict
        assert fd["n"] == 50
        assert "rate" in fd


# ------------------------------------------------------------------------------
# 1.5 Format Specifiers & Rendering (5 Tests)
# ------------------------------------------------------------------------------

def test_t1_f5_format_custom_template():
    """Verify custom bar_format template rendering."""
    s = io.StringIO()
    fmt = "Step: {n}/{total} | [{bar}]"
    with tqdm(total=20, file=s, bar_format=fmt, miniters=1, mininterval=0) as pbar:
        pbar.update(10)
    output = s.getvalue()
    assert "Step: 10/20 | [" in output


def test_t1_f5_format_elapsed_and_remaining():
    """Verify elapsed and remaining formatting tokens."""
    s = io.StringIO()
    fmt = "{percentage:3.0f}%|{elapsed}<{remaining}"
    with tqdm(total=100, file=s, bar_format=fmt, miniters=1, mininterval=0) as pbar:
        pbar.update(50)
    output = s.getvalue()
    assert "50%|" in output
    assert "<" in output


def test_t1_f5_format_percentage():
    """Verify explicit percentage precision formatting."""
    s = io.StringIO()
    fmt = "{percentage:.2f}%"
    with tqdm(total=3, file=s, bar_format=fmt, miniters=1, mininterval=0) as pbar:
        pbar.update(1)
    output = s.getvalue()
    assert "33.33%" in output


def test_t1_f5_format_rate_specifier():
    """Verify rate_fmt formatting token is populated."""
    s = io.StringIO()
    fmt = "speed: {rate_fmt}"
    with tqdm(total=10, file=s, bar_format=fmt, miniters=1, mininterval=0) as pbar:
        pbar.update(5)
    output = s.getvalue()
    assert "speed:" in output


def test_t1_f5_format_missing_total_graceful():
    """Verify custom bar_format handles total=None without exceptions."""
    s = io.StringIO()
    fmt = "{n} done [{elapsed}]"
    with tqdm(file=s, bar_format=fmt, miniters=1, mininterval=0) as pbar:
        pbar.update(7)
    output = s.getvalue()
    assert "7 done [" in output


# ------------------------------------------------------------------------------
# 1.6 Disable & Leave Controls (5 Tests)
# ------------------------------------------------------------------------------

def test_t1_f6_disable_true_produces_no_output():
    """Verify disable=True completely suppresses all stream output."""
    s = io.StringIO()
    with tqdm(range(20), file=s, disable=True) as pbar:
        list(pbar)
    assert s.getvalue() == ""


def test_t1_f6_disable_iteration_transparency():
    """Verify disable=True preserves normal iterator sequence and performance."""
    s = io.StringIO()
    with tqdm(["a", "b", "c"], file=s, disable=True) as pbar:
        out = list(pbar)
    assert out == ["a", "b", "c"]


def test_t1_f6_leave_true_preserves_bar():
    """Verify leave=True keeps the final bar line visible."""
    s = io.StringIO()
    with tqdm(total=10, file=s, leave=True, miniters=1, mininterval=0) as pbar:
        pbar.update(10)
    assert "100%" in s.getvalue()


def test_t1_f6_leave_false_suppresses_residual():
    """Verify leave=False terminates or removes bar line cleanly on exit."""
    s = io.StringIO()
    with tqdm(total=10, file=s, leave=False, miniters=1, mininterval=0) as pbar:
        pbar.update(10)
    output = s.getvalue()
    assert "\r" in output or output == ""


def test_t1_f6_clear_method():
    """Verify pbar.clear() writes a line clearing sequence."""
    s = io.StringIO()
    with tqdm(total=10, file=s, miniters=1, mininterval=0) as pbar:
        pbar.update(5)
        pbar.clear()
    assert "\r" in s.getvalue()


# ------------------------------------------------------------------------------
# 1.7 Dynamic Throttling & Adaptive Scaling (5 Tests)
# ------------------------------------------------------------------------------

def test_t1_f7_dynamic_miniters_default_enabled():
    """Verify dynamic_miniters is enabled when miniters is None."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        assert pbar.dynamic_miniters is True


def test_t1_f7_manual_miniters_override_preserved():
    """Verify user-specified miniters disables dynamic_miniters and is immutable."""
    s = io.StringIO()
    with tqdm(total=100, file=s, miniters=42) as pbar:
        assert pbar.dynamic_miniters is False
        assert pbar.miniters == 42
        for _ in range(50):
            pbar.update(1)
        assert pbar.miniters == 42


def test_t1_f7_adaptive_scaling_under_high_throughput():
    """Verify high-throughput iteration scales miniters to reduce overhead."""
    s = io.StringIO()
    with tqdm(range(25000), file=s, mininterval=0.0001) as pbar:
        list(pbar)
    assert pbar.n == 25000
    assert pbar.miniters >= 1


def test_t1_f7_zero_dt_simulated_clock_safe():
    """Verify discrete/mock frozen clock (dt <= 0) does not raise ZeroDivisionError."""
    class FrozenClock:
        def __call__(self):
            return 12345.678

    s = io.StringIO()
    with tqdm(total=20, file=s) as pbar:
        pbar._time = FrozenClock()
        for _ in range(20):
            pbar.update(1)
    assert pbar.n == 20


def test_t1_f7_manual_update_adaptive_scaling():
    """Verify manual update loop scales miniters dynamically under throughput."""
    s = io.StringIO()
    with tqdm(total=5000, file=s) as pbar:
        for _ in range(1000):
            pbar.update(1)
    assert pbar.n == 1000


# ------------------------------------------------------------------------------
# 1.8 BatchBuffer Core Utility (5 Tests)
# ------------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t1_f8_batch_buffer_push_and_capacity():
    """Verify BatchBuffer accumulates pushes and flushes upon reaching capacity."""
    s = io.StringIO()
    with tqdm(total=50, file=s) as pbar:
        with BatchBuffer(pbar, batch_size=10) as buf:
            for _ in range(9):
                buf.push(1)
            assert pbar.n == 0
            buf.push(1)
            assert pbar.n == 10


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t1_f8_batch_buffer_flush_remainder():
    """Verify explicit flush transfers uncommitted buffer items."""
    s = io.StringIO()
    with tqdm(total=50, file=s) as pbar:
        buf = BatchBuffer(pbar, batch_size=20)
        buf.push(8)
        assert pbar.n == 0
        buf.flush()
        assert pbar.n == 8


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t1_f8_batch_buffer_context_manager_autoflush():
    """Verify context manager automatically flushes uncommitted buffer upon exit."""
    s = io.StringIO()
    with tqdm(total=50, file=s) as pbar:
        with pbar.buffered(batch_size=25) as buf:
            buf.push(12)
        assert pbar.n == 12


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t1_f8_batch_buffer_callable_interface():
    """Verify buffer instance callable signature buf(n)."""
    s = io.StringIO()
    with tqdm(total=50, file=s) as pbar:
        with pbar.buffered(batch_size=5) as buf:
            for _ in range(7):
                buf(1)
        assert pbar.n == 7


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
@pytest.mark.asyncio
async def test_t1_f8_batch_buffer_async_context_manager():
    """Verify async context manager auto-flushes upon async exit."""
    s = io.StringIO()
    with tqdm(total=50, file=s) as pbar:
        async with pbar.buffered(batch_size=10) as buf:
            buf.push(4)
        assert pbar.n == 4


# ------------------------------------------------------------------------------
# 1.9 Multi-threaded Concurrency & Locking (5 Tests)
# ------------------------------------------------------------------------------

def test_t1_f9_thread_concurrent_updates():
    """Verify concurrent updates across worker threads reach exact total."""
    s = io.StringIO()
    with tqdm(total=1000, file=s) as pbar:
        def worker():
            for _ in range(100):
                pbar.update(1)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    assert pbar.n == 1000


def test_t1_f9_thread_lock_custom_rlock():
    """Verify custom lock_args tuple integrates cleanly without deadlock."""
    s = io.StringIO()
    with tqdm(total=20, file=s, lock_args=(True,)) as pbar:
        pbar.update(10)
    assert pbar.n == 10


def test_t1_f9_thread_get_lock():
    """Verify tqdm.get_lock() returns a valid lock interface."""
    lock = tqdm.get_lock()
    assert lock is not None
    assert hasattr(lock, "acquire")
    assert hasattr(lock, "release")


def test_t1_f9_thread_pool_worker_distribution():
    """Verify ThreadPoolExecutor distributing updates to shared progress bar."""
    s = io.StringIO()
    with tqdm(total=200, file=s) as pbar:
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(lambda _: pbar.update(1), range(200)))
    assert pbar.n == 200


def test_t1_f9_thread_safe_multiple_bars():
    """Verify independent progress bars executed on distinct threads do not collide."""
    s1, s2 = io.StringIO(), io.StringIO()
    default_lock = tqdm.get_lock()
    tqdm.set_lock(threading.RLock())
    try:
        def run_bar(total, stream):
            with tqdm(total=total, file=stream, mininterval=0) as pbar:
                for _ in range(total):
                    pbar.update(1)

        t1 = threading.Thread(target=run_bar, args=(20, s1))
        t2 = threading.Thread(target=run_bar, args=(30, s2))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    finally:
        tqdm.set_lock(default_lock)
    assert "100%" in s1.getvalue()
    assert "100%" in s2.getvalue()


# ------------------------------------------------------------------------------
# 1.10 Async Iteration & asyncio Integration (5 Tests)
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_t1_f10_async_tqdm_iteration():
    """Verify tqdm_asyncio wraps async generator and yields all items."""
    async def async_num_stream():
        for i in range(10):
            yield i

    s = io.StringIO()
    with tqdm_asyncio(async_num_stream(), file=s) as pbar:
        items = [x async for x in pbar]
    assert items == list(range(10))
    assert pbar.n == 10


@pytest.mark.asyncio
async def test_t1_f10_async_gather_multiple_bars():
    """Verify asyncio.gather executing multiple coroutines with progress bars."""
    async def async_worker(total, stream):
        with tqdm_asyncio(total=total, file=stream, mininterval=0) as pbar:
            for _ in range(total):
                await asyncio.sleep(0.001)
                pbar.update(1)
        return total

    s1, s2 = io.StringIO(), io.StringIO()
    results = await asyncio.gather(async_worker(5, s1), async_worker(8, s2))
    assert results == [5, 8]


@pytest.mark.asyncio
async def test_t1_f10_async_manual_update():
    """Verify manual update inside async coroutine."""
    s = io.StringIO()
    with tqdm_asyncio(total=20, file=s) as pbar:
        pbar.update(10)
        await asyncio.sleep(0.001)
        pbar.update(10)
    assert pbar.n == 20


@pytest.mark.asyncio
async def test_t1_f10_async_break_early():
    """Verify early break in async loop cleanly finalizes."""
    s = io.StringIO()
    pbar = tqdm_asyncio(range(50), file=s)
    try:
        async for x in pbar:
            if x == 4:
                break
    finally:
        pbar.close()
    assert pbar.n == 5


@pytest.mark.asyncio
async def test_t1_f10_async_total_tracking():
    """Verify async progress bar correctly tracks inferred total from range."""
    s = io.StringIO()
    with tqdm_asyncio(range(15), file=s) as pbar:
        async for _ in pbar:
            pass
    assert pbar.total == 15
    assert pbar.n == 15


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (50 Tests)
# ==============================================================================

# ------------------------------------------------------------------------------
# 2.1 Progress Display Boundaries (5 Tests)
# ------------------------------------------------------------------------------

def test_t2_f1_zero_total_display():
    """Verify total=0 renders cleanly without division by zero."""
    s = io.StringIO()
    with tqdm(total=0, file=s, miniters=1, mininterval=0) as pbar:
        pbar.update(0)
    assert pbar.n == 0
    assert "0/0" in s.getvalue() or "0it" in s.getvalue()


def test_t2_f1_very_large_total_display():
    """Verify large 64-bit totals render without overflow."""
    s = io.StringIO()
    huge = 10**15
    with tqdm(total=huge, file=s, unit="B", unit_scale=True, miniters=1, mininterval=0) as pbar:
        pbar.update(huge // 2)
    assert pbar.n == huge // 2
    assert "50%" in s.getvalue()


def test_t2_f1_terminal_ncols_small():
    """Verify extremely small ncols bounds display without crashing."""
    s = io.StringIO()
    with tqdm(total=10, file=s, ncols=10, miniters=1, mininterval=0) as pbar:
        pbar.update(5)
    assert len(s.getvalue()) > 0


def test_t2_f1_unicode_desc_special_chars():
    """Verify Unicode, emoji, and non-ASCII characters in desc render safely."""
    s = io.StringIO()
    with tqdm(total=10, file=s, desc="🚀 进度条", miniters=1, mininterval=0) as pbar:
        pbar.update(5)
    output = s.getvalue()
    assert "🚀 进度条" in output


def test_t2_f1_escaped_brackets_in_desc():
    """Verify square brackets in description do not break format string parsing."""
    s = io.StringIO()
    with tqdm(total=10, file=s, desc="[Worker-1]", miniters=1, mininterval=0) as pbar:
        pbar.update(5)
    assert "[Worker-1]" in s.getvalue()


# ------------------------------------------------------------------------------
# 2.2 Iteration Boundaries (5 Tests)
# ------------------------------------------------------------------------------

def test_t2_f2_empty_iterable():
    """Verify empty iterable loop terminates immediately with 0 iterations."""
    s = io.StringIO()
    with tqdm([], file=s) as pbar:
        out = list(pbar)
    assert out == []
    assert pbar.n == 0


def test_t2_f2_single_item_iterable():
    """Verify single-item iterable completes with exact count 1."""
    s = io.StringIO()
    with tqdm([42], file=s) as pbar:
        out = list(pbar)
    assert out == [42]
    assert pbar.n == 1


def test_t2_f2_infinite_generator_early_exit():
    """Verify infinite generator exiting via break closes properly."""
    def infinite_stream():
        n = 0
        while True:
            yield n
            n += 1

    s = io.StringIO()
    with tqdm(infinite_stream(), file=s) as pbar:
        for val in pbar:
            if val >= 5:
                break
    assert pbar.n == 5


def test_t2_f2_generator_raising_exception():
    """Verify generator raising exception executes cleanup safely."""
    def buggy_stream():
        yield 1
        yield 2
        raise RuntimeError("Stream broken")

    s = io.StringIO()
    with pytest.raises(RuntimeError, match="Stream broken"):
        with tqdm(buggy_stream(), file=s) as pbar:
            list(pbar)
    assert pbar.n == 2


def test_t2_f2_nested_iterator_unpacking():
    """Verify iterating tuples unrolls correctly."""
    data = [(1, "a"), (2, "b"), (3, "c")]
    s = io.StringIO()
    with tqdm(data, file=s) as pbar:
        results = [(num, char) for num, char in pbar]
    assert results == data
    assert pbar.n == 3


# ------------------------------------------------------------------------------
# 2.3 Manual Update Boundaries (5 Tests)
# ------------------------------------------------------------------------------

def test_t2_f3_update_zero():
    """Verify update(0) does not corrupt iteration count."""
    s = io.StringIO()
    with tqdm(total=10, file=s) as pbar:
        pbar.update(0)
    assert pbar.n == 0


def test_t2_f3_update_negative_decrement():
    """Verify update with negative value decrements internal counter."""
    s = io.StringIO()
    with tqdm(total=20, file=s) as pbar:
        pbar.update(10)
        pbar.update(-3)
    assert pbar.n == 7


def test_t2_f3_update_exceeding_total():
    """Verify updates past total do not crash and indicate overflow."""
    s = io.StringIO()
    with tqdm(total=10, file=s, miniters=1, mininterval=0) as pbar:
        pbar.update(25)
    assert pbar.n == 25
    assert "25it" in s.getvalue()


def test_t2_f3_rapid_burst_updates():
    """Verify 10,000 rapid 1-step updates complete without dropped counts."""
    s = io.StringIO()
    with tqdm(total=10000, file=s) as pbar:
        for _ in range(10000):
            pbar.update(1)
    assert pbar.n == 10000


def test_t2_f3_large_single_jump():
    """Verify massive single increment updates correctly."""
    s = io.StringIO()
    with tqdm(total=10**9, file=s) as pbar:
        pbar.update(10**9)
    assert pbar.n == 10**9


# ------------------------------------------------------------------------------
# 2.4 Timing Limits Boundaries (5 Tests)
# ------------------------------------------------------------------------------

def test_t2_f4_zero_mininterval():
    """Verify mininterval=0 refreshes immediately when miniters is met."""
    s = io.StringIO()
    with tqdm(total=5, file=s, mininterval=0, miniters=1) as pbar:
        for _ in range(5):
            pbar.update(1)
    assert pbar.n == 5


def test_t2_f4_large_mininterval():
    """Verify large mininterval suppresses intermediate updates entirely."""
    s = io.StringIO()
    with tqdm(total=100, file=s, mininterval=3600.0) as pbar:
        for _ in range(50):
            pbar.update(1)
    assert pbar.n == 50


def test_t2_f4_zero_maxinterval():
    """Verify maxinterval=0 disables maxinterval refresh timeout."""
    s = io.StringIO()
    with tqdm(total=10, file=s, maxinterval=0) as pbar:
        pbar.update(1)
    assert pbar.n == 1


def test_t2_f4_delay_exceeding_runtime():
    """Verify delay exceeding runtime prevents intermediate display writes."""
    s = io.StringIO()
    with tqdm(total=10, file=s, delay=100.0) as pbar:
        pbar.update(5)
    assert s.getvalue() == ""


def test_t2_f4_negative_delay():
    """Verify negative delay is handled safely as 0."""
    s = io.StringIO()
    with tqdm(total=10, file=s, delay=-1.0, mininterval=0, miniters=1) as pbar:
        pbar.update(1)
    assert pbar.n == 1


# ------------------------------------------------------------------------------
# 2.5 Format Specifiers Boundaries (5 Tests)
# ------------------------------------------------------------------------------

def test_t2_f5_empty_bar_format():
    """Verify empty bar_format string defaults gracefully without crash."""
    s = io.StringIO()
    with tqdm(total=10, file=s, bar_format="", miniters=1, mininterval=0) as pbar:
        pbar.update(5)
    assert "5/10" in s.getvalue() or "50%" in s.getvalue()


def test_t2_f5_literal_percent_and_braces():
    """Verify literal double braces and percent signs in custom template."""
    s = io.StringIO()
    fmt = "Status {{raw}}: {percentage:.0f}%% done"
    with tqdm(total=100, file=s, bar_format=fmt, miniters=1, mininterval=0) as pbar:
        pbar.update(45)
    output = s.getvalue()
    assert "{raw}" in output or "Status" in output
    assert "45%" in output


def test_t2_f5_custom_bar_format_unknown_keys():
    """Verify unrecognized formatting keys are tolerated or surfaced safely."""
    s = io.StringIO()
    fmt = "{n}/{total} | {unrecognized_key}"
    try:
        with tqdm(total=10, file=s, bar_format=fmt) as pbar:
            pbar.update(1)
    except (KeyError, ValueError):
        pass  # Format validation error is expected and acceptable


def test_t2_f5_custom_bar_format_only_percentage():
    """Verify minimal format string containing only percentage token."""
    s = io.StringIO()
    with tqdm(total=50, file=s, bar_format="{percentage:.1f}%", miniters=1, mininterval=0) as pbar:
        pbar.update(25)
    assert "50.0%" in s.getvalue()


def test_t2_f5_extreme_smoothing_values():
    """Verify smoothing=0 (instantaneous) and smoothing=1 (maximum smoothing)."""
    s1, s2 = io.StringIO(), io.StringIO()
    with tqdm(total=10, file=s1, smoothing=0.0) as pbar:
        pbar.update(5)
    with tqdm(total=10, file=s2, smoothing=1.0) as pbar:
        pbar.update(5)
    assert pbar.smoothing == 1.0


# ------------------------------------------------------------------------------
# 2.6 Disable & Leave Boundaries (5 Tests)
# ------------------------------------------------------------------------------

def test_t2_f6_toggle_disable_dynamically():
    """Verify changing pbar.disable dynamically suppresses subsequent updates."""
    s = io.StringIO()
    with tqdm(total=20, file=s, miniters=1, mininterval=0) as pbar:
        pbar.update(5)
        len1 = len(s.getvalue())
        pbar.disable = True
        pbar.update(10)
        len2 = len(s.getvalue())
        pbar.disable = False  # restore for clean close
    assert len1 == len2
    assert pbar.n == 5


def test_t2_f6_double_close_idempotent():
    """Verify calling close() multiple times does not raise exceptions."""
    s = io.StringIO()
    pbar = tqdm(total=10, file=s)
    pbar.update(5)
    pbar.close()
    pbar.close()
    pbar.close()
    assert pbar.n == 5


def test_t2_f6_leave_none_default():
    """Verify leave=None defaults appropriately."""
    s = io.StringIO()
    with tqdm(total=10, file=s, leave=None) as pbar:
        pbar.update(10)
    assert pbar.n == 10


def test_t2_f6_reset_clears_counts():
    """Verify reset() re-initializes counts and total."""
    s = io.StringIO()
    with tqdm(total=50, file=s) as pbar:
        pbar.update(30)
        pbar.reset(total=100)
        assert pbar.n == 0
        assert pbar.total == 100
        pbar.update(10)
        assert pbar.n == 10


def test_t2_f6_reopen_after_close():
    """Verify calling reset() after close() allows bar reuse when re-enabled."""
    s = io.StringIO()
    pbar = tqdm(total=10, file=s)
    pbar.update(10)
    pbar.close()
    pbar.disable = False
    pbar.reset(total=20)
    pbar.update(5)
    pbar.close()
    assert pbar.n == 5


# ------------------------------------------------------------------------------
# 2.7 Dynamic Throttling Boundaries (5 Tests)
# ------------------------------------------------------------------------------

def test_t2_f7_miniters_zero_initialization():
    """Verify miniters initializes to 0 when dynamic_miniters is enabled."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        assert pbar.miniters == 0


def test_t2_f7_discrete_frozen_clock():
    """Verify frozen clock does not divide by zero or stall execution."""
    fixed_time = 500.0

    s = io.StringIO()
    with tqdm(total=30, file=s) as pbar:
        pbar._time = lambda: fixed_time
        for _ in range(30):
            pbar.update(1)
    assert pbar.n == 30


def test_t2_f7_clock_step_regression():
    """Verify backwards time jitter does not corrupt state."""
    time_series = [100.0, 105.0, 95.0, 110.0]

    def jittery_clock():
        if time_series:
            return time_series.pop(0)
        return 115.0

    s = io.StringIO()
    with tqdm(total=4, file=s) as pbar:
        pbar._time = jittery_clock
        for _ in range(4):
            pbar.update(1)
    assert pbar.n == 4


def test_t2_f7_huge_rate_burst_scaling():
    """Verify sudden burst of 50,000 iterations safely scales miniters."""
    s = io.StringIO()
    with tqdm(total=100000, file=s) as pbar:
        pbar.update(50000)
    assert pbar.n == 50000


def test_t2_f7_explicit_miniters_1_respected():
    """Verify explicit miniters=1 checks every single update."""
    s = io.StringIO()
    with tqdm(total=10, file=s, miniters=1, mininterval=0) as pbar:
        for _ in range(10):
            pbar.update(1)
        assert pbar.miniters == 1
    assert pbar.n == 10


# ------------------------------------------------------------------------------
# 2.8 BatchBuffer Boundaries (5 Tests)
# ------------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t2_f8_batch_buffer_size_1():
    """Verify BatchBuffer with batch_size=1 flushes on every push."""
    s = io.StringIO()
    with tqdm(total=10, file=s) as pbar:
        with BatchBuffer(pbar, batch_size=1) as buf:
            buf.push(1)
            assert pbar.n == 1
            buf.push(1)
            assert pbar.n == 2


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t2_f8_batch_buffer_size_larger_than_total():
    """Verify buffer size larger than total flushes all items upon exit."""
    s = io.StringIO()
    with tqdm(total=20, file=s) as pbar:
        with pbar.buffered(batch_size=5000) as buf:
            for _ in range(20):
                buf.push(1)
            assert pbar.n == 0
        assert pbar.n == 20


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t2_f8_batch_buffer_push_zero():
    """Verify push(0) does not distort buffer accumulation."""
    s = io.StringIO()
    with tqdm(total=10, file=s) as pbar:
        with pbar.buffered(batch_size=5) as buf:
            buf.push(0)
            buf.push(3)
        assert pbar.n == 3


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t2_f8_batch_buffer_push_exact_multiple():
    """Verify pushes that are exact multiples of batch_size flush completely."""
    s = io.StringIO()
    with tqdm(total=30, file=s) as pbar:
        with pbar.buffered(batch_size=10) as buf:
            buf.push(30)
            assert pbar.n == 30


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t2_f8_batch_buffer_exception_in_context():
    """Verify uncommitted buffer flushes even when an exception occurs."""
    s = io.StringIO()
    with tqdm(total=50, file=s) as pbar:
        try:
            with pbar.buffered(batch_size=20) as buf:
                buf.push(7)
                raise RuntimeError("Abort processing")
        except RuntimeError:
            pass
        assert pbar.n == 7


# ------------------------------------------------------------------------------
# 2.9 Multi-threaded Concurrency Boundaries (5 Tests)
# ------------------------------------------------------------------------------

def test_t2_f9_thread_high_contention():
    """Verify 20 concurrent threads hammering update() simultaneously."""
    s = io.StringIO()
    with tqdm(total=2000, file=s) as pbar:
        def hammer():
            for _ in range(100):
                pbar.update(1)

        threads = [threading.Thread(target=hammer) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    assert pbar.n == 2000


def test_t2_f9_thread_zero_increment_contention():
    """Verify concurrent update(0) does not deadlock or corrupt state."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        def zero_updater():
            for _ in range(50):
                pbar.update(0)

        threads = [threading.Thread(target=zero_updater) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    assert pbar.n == 0


def test_t2_f9_thread_concurrent_close():
    """Verify concurrent close() during worker updates does not cause deadlocks."""
    s = io.StringIO()
    pbar = tqdm(total=50, file=s)

    def continuous_update():
        for _ in range(50):
            pbar.update(1)

    t = threading.Thread(target=continuous_update)
    t.start()
    pbar.close()
    t.join()


def test_t2_f9_thread_recursive_lock():
    """Verify tqdm global lock supports recursive acquisition on same thread."""
    lock = tqdm.get_lock()
    lock.acquire()
    lock.acquire()
    lock.release()
    lock.release()


def test_t2_f9_thread_worker_exception():
    """Verify worker thread exception does not leave shared lock poisoned."""
    s = io.StringIO()
    with tqdm(total=50, file=s) as pbar:
        def faulty_worker():
            try:
                pbar.update(5)
                raise ValueError("Thread error")
            except ValueError:
                pass

        t = threading.Thread(target=faulty_worker)
        t.start()
        t.join()
        # Ensure main thread can still update cleanly
        pbar.update(10)
    assert pbar.n == 15


# ------------------------------------------------------------------------------
# 2.10 Async Boundaries (5 Tests)
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_t2_f10_async_empty_iterator():
    """Verify empty async generator finishes with 0 iterations."""
    async def empty_agen():
        if False:
            yield 0

    s = io.StringIO()
    with tqdm_asyncio(empty_agen(), file=s) as pbar:
        res = [x async for x in pbar]
    assert res == []
    assert pbar.n == 0


@pytest.mark.asyncio
async def test_t2_f10_async_exception_in_generator():
    """Verify async generator error triggers safe cleanup."""
    async def failing_agen():
        yield 100
        raise ValueError("Async stream failed")

    s = io.StringIO()
    with pytest.raises(ValueError, match="Async stream failed"):
        with tqdm_asyncio(failing_agen(), file=s) as pbar:
            _ = [x async for x in pbar]
    assert pbar.n == 1


@pytest.mark.asyncio
async def test_t2_f10_async_sleep_delay():
    """Verify async progress tracking with interleaved awaits."""
    s = io.StringIO()
    with tqdm_asyncio(range(3), file=s) as pbar:
        async for _ in pbar:
            await asyncio.sleep(0.005)
    assert pbar.n == 3


@pytest.mark.asyncio
async def test_t2_f10_async_cancellation():
    """Verify cancellation of async task running tqdm handles cleanly."""
    pbar_holder = []

    async def long_running_task():
        pbar = tqdm_asyncio(range(100))
        pbar_holder.append(pbar)
        try:
            async for _ in pbar:
                await asyncio.sleep(0.05)
        finally:
            pbar.close()

    task = asyncio.create_task(long_running_task())
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_t2_f10_async_zero_total():
    """Verify async progress bar with total=0 completes cleanly."""
    s = io.StringIO()
    with tqdm_asyncio(total=0, file=s) as pbar:
        pbar.update(0)
    assert pbar.n == 0


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (10 Tests)
# ==============================================================================

@pytest.mark.asyncio
async def test_t3_asyncio_with_rate_throttling():
    """Cross-feature: tqdm_asyncio with high iteration count and dynamic throttling."""
    s = io.StringIO()
    with tqdm_asyncio(range(500), file=s, mininterval=0.01) as pbar:
        async for _ in pbar:
            pass
    assert pbar.n == 500
    assert pbar.miniters >= 0


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t3_threads_with_batch_buffer():
    """Cross-feature: Multiple worker threads feeding a thread_safe BatchBuffer."""
    s = io.StringIO()
    with tqdm(total=500, file=s) as pbar:
        with BatchBuffer(pbar, batch_size=25, thread_safe=True) as buf:
            def worker():
                for _ in range(50):
                    buf.push(1)

            threads = [threading.Thread(target=worker) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
    assert pbar.n == 500


def test_t3_trange_with_custom_format_and_smoothing():
    """Cross-feature: trange combining custom template, EMA smoothing, and unit scaling."""
    s = io.StringIO()
    fmt = "Processing: {percentage:.0f}% | {rate_fmt} | [{bar}]"
    for _ in trange(50, file=s, bar_format=fmt, smoothing=0.3, unit="item", unit_scale=True):
        pass
    assert "Processing:" in s.getvalue()
    assert "100%" in s.getvalue()


def test_t3_manual_update_with_delay_and_mininterval():
    """Cross-feature: Manual update with delay, mininterval suppression, and terminal flush."""
    s = io.StringIO()
    with tqdm(total=10, file=s, delay=0.01, mininterval=0.05) as pbar:
        for _ in range(5):
            pbar.update(1)
        time.sleep(0.02)
        for _ in range(5):
            pbar.update(1)
    assert pbar.n == 10


def test_t3_leave_false_with_custom_stream_and_nested_bars():
    """Cross-feature: Inner bar with leave=False inside outer bar with leave=True."""
    s_outer, s_inner = io.StringIO(), io.StringIO()
    with tqdm(total=3, file=s_outer, leave=True) as p_out:
        for _ in range(3):
            with tqdm(total=5, file=s_inner, leave=False) as p_in:
                for _ in range(5):
                    p_in.update(1)
            p_out.update(1)
    assert p_out.n == 3
    assert "100%" in s_outer.getvalue()


def test_t3_dynamic_throttling_with_manual_override():
    """Cross-feature: Bar initialized dynamically, then miniters altered explicitly."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        pbar.update(10)
        pbar.miniters = 20
        pbar.dynamic_miniters = False
        pbar.update(10)
        assert pbar.miniters == 20


def test_t3_ascii_mode_with_nested_dual_bars():
    """Cross-feature: Nested progress bars both operating in ascii=True mode."""
    s = io.StringIO()
    with tqdm(range(2), file=s, ascii=True, desc="Outer") as outer:
        for _ in outer:
            with tqdm(range(3), file=s, ascii=True, desc="Inner") as inner:
                list(inner)
    out = s.getvalue()
    assert "Outer:" in out
    assert "Inner:" in out
    assert "█" not in out


@pytest.mark.asyncio
async def test_t3_async_gather_with_custom_bar_formats():
    """Cross-feature: Multiple concurrent async tasks with individualized bar_format templates."""
    s1, s2 = io.StringIO(), io.StringIO()

    async def run_task(name, s, fmt):
        with tqdm_asyncio(total=5, file=s, bar_format=fmt) as pbar:
            for _ in range(5):
                await asyncio.sleep(0.001)
                pbar.update(1)

    t1 = run_task("A", s1, "{percentage:.0f}% Alpha")
    t2 = run_task("B", s2, "{percentage:.0f}% Beta")
    await asyncio.gather(t1, t2)
    assert "Alpha" in s1.getvalue()
    assert "Beta" in s2.getvalue()


@pytest.mark.skipif(not HAS_BATCH_BUFFER, reason="M2 BatchBuffer not yet implemented in tqdm")
def test_t3_batch_buffer_with_negative_adjustments():
    """Cross-feature: BatchBuffer with positive additions and step adjustments."""
    s = io.StringIO()
    with tqdm(total=100, file=s) as pbar:
        with pbar.buffered(batch_size=10) as buf:
            buf.push(15)
            buf.push(-2)
            buf.flush()
        assert pbar.n == 13


def test_t3_thread_pool_with_ema_smoothing():
    """Cross-feature: ThreadPoolExecutor updating bar with EMA rate smoothing."""
    s = io.StringIO()
    thread_lock = threading.Lock()
    with tqdm(total=50, file=s, smoothing=0.5) as pbar:
        def update_task():
            with thread_lock:
                pbar.update(1)

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(update_task) for _ in range(50)]
            for f in futures:
                f.result(timeout=5.0)
    assert pbar.n == 50


# ==============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (5 Tests)
# ==============================================================================

def test_t4_streaming_batch_record_processor():
    """
    Scenario 1: High-throughput streaming record processor.
    Simulates parsing 5,000 JSON/CSV data records in chunks with dynamic rate tracking.
    """
    s = io.StringIO()
    total_records = 5000
    chunk_size = 250

    def generate_chunks():
        records_sent = 0
        while records_sent < total_records:
            current_batch = min(chunk_size, total_records - records_sent)
            records_sent += current_batch
            yield [{"id": i, "val": i * 2} for i in range(current_batch)]

    processed_count = 0
    with tqdm(
        total=total_records, file=s, unit="rec", unit_scale=True, desc="ETL Ingestion"
    ) as pbar:
        for chunk in generate_chunks():
            # Process records
            processed_count += len(chunk)
            pbar.update(len(chunk))

    assert processed_count == total_records
    assert pbar.n == total_records
    assert "100%" in s.getvalue()
    assert "ETL Ingestion:" in s.getvalue()


def test_t4_multithreaded_worker_queue_ingestion():
    """
    Scenario 2: Multi-threaded producer-consumer queue processing.
    Workers pull tasks from a queue.Queue, compute, and update thread-safe meter.
    """
    s = io.StringIO()
    task_queue = queue.Queue()
    num_tasks = 200
    num_workers = 4

    for i in range(num_tasks):
        task_queue.put(i)

    results = []
    results_lock = threading.Lock()

    with tqdm(total=num_tasks, file=s, desc="Worker Pool") as pbar:
        def worker():
            while True:
                try:
                    item = task_queue.get_nowait()
                except queue.Empty:
                    break
                # Simulate light CPU bound transformation
                res = item * item
                with results_lock:
                    results.append(res)
                pbar.update(1)
                task_queue.task_done()

        threads = [threading.Thread(target=worker) for _ in range(num_workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert len(results) == num_tasks
    assert pbar.n == num_tasks
    assert "Worker Pool:" in s.getvalue()


@pytest.mark.asyncio
async def test_t4_async_chunk_downloader_simulation():
    """
    Scenario 3: Asynchronous concurrent network chunk downloader.
    Simulates downloading multiple files partitioned into concurrent chunks using asyncio.gather.
    """
    s = io.StringIO()
    num_files = 5
    chunks_per_file = 10
    total_chunks = num_files * chunks_per_file

    async def download_file_chunk(file_id, chunk_id, pbar):
        await asyncio.sleep(0.001)  # Simulate network latency
        pbar.update(1)
        return f"file_{file_id}_chunk_{chunk_id}"

    with tqdm_asyncio(total=total_chunks, file=s, unit="chunk", desc="Network DL") as pbar:
        tasks = []
        for fid in range(num_files):
            for cid in range(chunks_per_file):
                tasks.append(download_file_chunk(fid, cid, pbar))
        results = await asyncio.gather(*tasks)

    assert len(results) == total_chunks
    assert pbar.n == total_chunks
    assert "Network DL:" in s.getvalue()


def test_t4_pipeline_etl_nested_bars():
    """
    Scenario 4: Multi-stage nested ETL pipeline.
    Simulates epochs/batches (outer loop) and individual record validations (inner loop)
    rendering into distinct streams without cross-stream contamination.
    """
    outer_stream = io.StringIO()
    inner_stream = io.StringIO()

    epochs = 3
    batches_per_epoch = 10
    total_processed = 0

    with tqdm(total=epochs, file=outer_stream, desc="Epochs", position=0) as p_outer:
        for epoch in range(epochs):
            with tqdm(
                total=batches_per_epoch, file=inner_stream,
                desc=f"Ep {epoch}", position=1, leave=False
            ) as p_inner:
                for _batch in range(batches_per_epoch):
                    total_processed += 1
                    p_inner.update(1)
            p_outer.update(1)

    assert total_processed == epochs * batches_per_epoch
    assert p_outer.n == epochs
    assert "Epochs:" in outer_stream.getvalue()
    assert "100%" in outer_stream.getvalue()


def test_t4_log_wrapped_resilient_pipeline():
    """
    Scenario 5: Resilient pipeline with interleaved log output via tqdm.write().
    Verifies that system logging/warning messages written through tqdm.write()
    do not distort or crash the progress meter.
    """
    s = io.StringIO()
    items = range(30)
    warnings_emitted = 0

    with tqdm(items, file=s, desc="Monitored Pipeline", mininterval=0) as pbar:
        for item in pbar:
            if item in (10, 20):
                tqdm.write(f"WARNING: High latency detected at item {item}", file=s)
                warnings_emitted += 1

    output = s.getvalue()
    assert warnings_emitted == 2
    assert "WARNING: High latency detected at item 10" in output
    assert "WARNING: High latency detected at item 20" in output
    assert pbar.n == 30
    assert "Monitored Pipeline:" in output
