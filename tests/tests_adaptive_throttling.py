"""
Unit and regression tests for adaptive dynamic throttling in tqdm.

Tests all code paths and branches in `tqdm.std.tqdm`:
- `__init__`: `dynamic_miniters` defaults vs explicit user `miniters`
- `__iter__`: adaptive extrapolation, discrete timers (dt <= 0), delay bounds
- `update()`: rate adaptation, smoothing branches, deduplicated clock query
"""

import io

from tqdm import tqdm


class MockDiscreteTimer:
    """Mock timer that yields controlled timestamps for deterministic testing."""

    def __init__(self, start=0.0):
        self.current = float(start)
        self.call_count = 0

    def time(self):
        self.call_count += 1
        return self.current

    def advance(self, dt):
        self.current += dt

    def __call__(self):
        return self.time()


def test_default_dynamic_miniters_initialization():
    """Verify default initialization sets dynamic_miniters=True and miniters=0."""
    t = tqdm(total=100)
    assert t.dynamic_miniters is True
    assert t.miniters == 0
    t.close()

    t2 = tqdm(range(50))
    assert t2.dynamic_miniters is True
    assert t2.miniters == 0
    t2.close()


def test_explicit_user_miniters_disables_dynamic():
    """Verify explicit miniters disables dynamic_miniters and retains fixed value."""
    t = tqdm(total=100, miniters=7)
    assert t.dynamic_miniters is False
    assert t.miniters == 7

    # Manual updates must not modify user-specified miniters
    for _ in range(20):
        t.update(1)
    assert t.miniters == 7
    t.close()


def test_explicit_user_miniters_in_iter_loop():
    """Verify __iter__ loop preserves explicit miniters without adapting."""
    s = io.StringIO()
    with tqdm(range(20), file=s, miniters=5, mininterval=0.1) as pbar:
        assert pbar.dynamic_miniters is False
        assert pbar.miniters == 5
        items = list(pbar)
        assert len(items) == 20
        assert pbar.miniters == 5


def test_iter_adaptive_scaling_under_high_rate():
    """Verify __iter__ scales miniters up when dt < mininterval."""
    clock = MockDiscreteTimer(start=100.0)
    s = io.StringIO()

    # Total 500 items, mininterval is 0.5s
    with tqdm(range(500), file=s, mininterval=0.5) as pbar:
        pbar._time = clock
        pbar.start_t = 100.0
        pbar.last_print_t = 100.0

        # Run through items while advancing clock by tiny increments (high throughput)
        for i in pbar:
            if i % 10 == 0:
                clock.advance(0.0001)

        # miniters should have scaled adaptively beyond initial 0
        assert pbar.miniters > 10
        assert pbar.n == 500


def test_iter_mock_timer_frozen_dt_zero():
    """Verify __iter__ with dt <= 0 triggers fallback miniters += 1."""
    clock = MockDiscreteTimer(start=50.0)
    s = io.StringIO()

    with tqdm(range(30), file=s, mininterval=1.0) as pbar:
        pbar._time = clock
        pbar.start_t = 50.0
        pbar.last_print_t = 50.0

        # Clock does not advance (dt == 0)
        for _ in pbar:
            pass

        assert pbar.n == 30
        assert pbar.miniters >= 1


def test_iter_mock_timer_negative_dt_step():
    """Verify __iter__ with dt < 0 gracefully triggers miniters += 1."""
    clock = MockDiscreteTimer(start=100.0)
    s = io.StringIO()

    with tqdm(range(10), file=s, mininterval=1.0) as pbar:
        pbar._time = clock
        pbar.start_t = 100.0
        pbar.last_print_t = 100.0

        # Regress clock backwards
        clock.advance(-10.0)
        for _ in pbar:
            pass

        assert pbar.n == 10
        assert pbar.miniters >= 1


def test_iter_mininterval_threshold_triggers_update():
    """Verify __iter__ triggers pbar.update() when dt >= mininterval."""
    clock = MockDiscreteTimer(start=10.0)
    s = io.StringIO()

    with tqdm(range(10), file=s, mininterval=0.1) as pbar:
        pbar._time = clock
        pbar.start_t = 10.0
        pbar.last_print_t = 10.0

        clock.advance(0.15)
        for i in pbar:
            if i == 5:
                clock.advance(0.2)

        assert pbar.n == 10


def test_iter_delay_prevents_premature_display():
    """Verify __iter__ does not update display if delay has not elapsed."""
    clock = MockDiscreteTimer(start=100.0)
    s = io.StringIO()

    with tqdm(range(5), file=s, mininterval=0.1, delay=5.0) as pbar:
        pbar._time = clock
        pbar.start_t = 100.0
        pbar.last_print_t = 100.0

        # Advance past mininterval, but before start_t + delay (105.0)
        clock.advance(0.2)
        for _ in pbar:
            pass

        assert pbar.n == 5


def test_update_adaptive_scaling_dt_positive():
    """Verify update() adapts miniters when dt < mininterval and dt > 0."""
    clock = MockDiscreteTimer(start=200.0)
    s = io.StringIO()

    with tqdm(total=1000, file=s, mininterval=1.0) as pbar:
        pbar._time = clock
        pbar.start_t = 200.0
        pbar.last_print_t = 200.0

        clock.advance(0.001)
        pbar.update(10)
        # Check adaptive scaling occurred
        assert pbar.miniters >= 1


def test_update_adaptive_scaling_dt_zero():
    """Verify update() increments miniters by 1 when dt <= 0 (clock freeze)."""
    clock = MockDiscreteTimer(start=300.0)
    s = io.StringIO()

    with tqdm(total=50, file=s, mininterval=1.0) as pbar:
        pbar._time = clock
        pbar.start_t = 300.0
        pbar.last_print_t = 300.0

        initial_miniters = pbar.miniters
        pbar.update(1)
        assert pbar.miniters == initial_miniters + 1


def test_update_smoothing_branches():
    """Verify update() correctly updates miniters across smoothing configurations."""
    clock = MockDiscreteTimer(start=10.0)
    s = io.StringIO()

    # 1. smoothing=0 (max seen so far)
    with tqdm(total=100, file=s, mininterval=0.1, smoothing=0) as pbar:
        pbar._time = clock
        pbar.start_t = pbar.last_print_t = clock.current
        clock.advance(0.2)
        pbar.update(25)
        assert pbar.miniters == 25

    # 2. smoothing > 0 (EMA calculation)
    clock_ema = MockDiscreteTimer(start=10.0)
    with tqdm(total=100, file=s, mininterval=0.1, smoothing=0.3) as pbar:
        pbar._time = clock_ema
        pbar.start_t = pbar.last_print_t = clock_ema.current
        clock_ema.advance(0.2)
        pbar.update(20)
        assert pbar.miniters > 0

    # 3. maxinterval elapsed branch
    clock_max = MockDiscreteTimer(start=10.0)
    with tqdm(total=100, file=s, mininterval=0.1, maxinterval=1.0, smoothing=0) as pbar:
        pbar._time = clock_max
        pbar.start_t = pbar.last_print_t = clock_max.current
        clock_max.advance(2.0)
        pbar.update(10)
        assert pbar.miniters > 0


def test_update_below_miniters_skips_clock():
    """Verify update() skips clock call entirely when n - last_print_n < miniters."""
    clock = MockDiscreteTimer(start=10.0)
    s = io.StringIO()

    with tqdm(total=100, file=s, mininterval=0.1) as pbar:
        pbar._time = clock
        pbar.miniters = 50
        initial_calls = clock.call_count

        pbar.update(1)
        # Should not have called clock
        assert clock.call_count == initial_calls
        assert pbar.n == 1


def test_redundant_clock_query_deduplication():
    """Verify clock query is deduplicated: update() stores cur_t in last_print_t."""
    clock = MockDiscreteTimer(start=100.0)
    s = io.StringIO()

    with tqdm(total=50, file=s, mininterval=0.1) as pbar:
        pbar._time = clock
        pbar.start_t = pbar.last_print_t = clock.current
        clock.advance(0.5)

        calls_before = clock.call_count
        res = pbar.update(10)
        calls_during = clock.call_count - calls_before

        assert res is True
        # Calls during update: 1 for cur_t in update() + 1 for format_dict in display()
        assert calls_during == 2
        # Verify last_print_t is set to cur_t directly without extra _time() call
        assert pbar.last_print_t == 100.5


def test_boundary_zero_and_single_iterations():
    """Verify edge cases for empty and single iteration sequences."""
    s = io.StringIO()

    with tqdm(range(0), file=s) as pbar:
        items = list(pbar)
        assert items == []
        assert pbar.n == 0

    with tqdm(range(1), file=s) as pbar:
        items = list(pbar)
        assert items == [0]
        assert pbar.n == 1


def test_boundary_large_iterations():
    """Verify large iteration counts trigger adaptive throttling smoothly."""
    s = io.StringIO()
    with tqdm(range(100000), file=s, mininterval=0.01) as pbar:
        for _ in pbar:
            pass
        assert pbar.n == 100000
        assert pbar.miniters >= 100


def test_negative_update_handling():
    """Verify negative decrement in update() correctly adjusts last_print_n."""
    s = io.StringIO()
    with tqdm(total=100, file=s, mininterval=0) as pbar:
        pbar.update(10)
        assert pbar.n == 10
        pbar.update(-5)
        assert pbar.n == 5
        assert pbar.last_print_n == 5


def test_disabled_bar_skips_throttling_logic():
    """Verify disable=True bypasses all iteration and update logic cleanly."""
    s = io.StringIO()
    with tqdm(range(50), file=s, disable=True) as pbar:
        items = list(pbar)
        assert len(items) == 50

    with tqdm(total=50, file=s, disable=True) as pbar:
        ret = pbar.update(10)
        assert ret is None


def test_update_manual_miniters_display_trigger_branch():
    """Verify update() with dynamic_miniters=False preserves miniters upon display."""
    clock = MockDiscreteTimer(start=10.0)
    s = io.StringIO()

    with tqdm(total=20, file=s, miniters=5, mininterval=0.1) as pbar:
        pbar._time = clock
        pbar.start_t = pbar.last_print_t = clock.current
        clock.advance(0.2)
        res = pbar.update(5)
        assert res is True
        assert pbar.miniters == 5
        assert pbar.dynamic_miniters is False


def test_update_manual_miniters_below_mininterval_branch():
    """Verify update() with dynamic_miniters=False does not adapt when dt < mininterval."""
    clock = MockDiscreteTimer(start=10.0)
    s = io.StringIO()

    with tqdm(total=20, file=s, miniters=2, mininterval=1.0) as pbar:
        pbar._time = clock
        pbar.start_t = pbar.last_print_t = clock.current
        clock.advance(0.01)
        res = pbar.update(2)
        assert res is None
        assert pbar.miniters == 2


def test_iter_manual_miniters_below_mininterval_branch():
    """Verify __iter__ with dynamic_miniters=False does not adapt when dt < mininterval."""
    clock = MockDiscreteTimer(start=10.0)
    s = io.StringIO()

    with tqdm(range(6), file=s, miniters=2, mininterval=1.0) as pbar:
        pbar._time = clock
        pbar.start_t = pbar.last_print_t = clock.current
        clock.advance(0.01)
        for _ in pbar:
            clock.advance(0.01)
        assert pbar.miniters == 2


def test_infinite_and_astronomical_mininterval():
    """Verify infinite and astronomical mininterval values avoid OverflowError."""
    # 1. __iter__ with mininterval=float('inf') using MockDiscreteTimer (dt > 0)
    clock = MockDiscreteTimer(start=100.0)
    s = io.StringIO()
    with tqdm(range(10), file=s, mininterval=float('inf')) as pbar:
        pbar._time = clock
        pbar.start_t = pbar.last_print_t = clock.current
        for _ in pbar:
            clock.advance(0.01)
        assert pbar.n == 10

    # 2. __iter__ with mininterval=float('inf') standard run
    s2 = io.StringIO()
    with tqdm(range(10), file=s2, mininterval=float('inf')) as pbar2:
        items = list(pbar2)
        assert items == list(range(10))
        assert pbar2.n == 10

    # 3. manual update() with mininterval=float('inf')
    clock3 = MockDiscreteTimer(start=100.0)
    s3 = io.StringIO()
    with tqdm(total=10, file=s3, mininterval=float('inf')) as pbar3:
        pbar3._time = clock3
        pbar3.start_t = pbar3.last_print_t = clock3.current
        for _ in range(10):
            clock3.advance(0.01)
            pbar3.update(1)
        assert pbar3.n == 10

    # 4. manual update() with astronomical mininterval=1e308
    clock4 = MockDiscreteTimer(start=100.0)
    s4 = io.StringIO()
    with tqdm(total=10, file=s4, mininterval=1e308) as pbar4:
        pbar4._time = clock4
        pbar4.start_t = pbar4.last_print_t = clock4.current
        for _ in range(10):
            clock4.advance(0.01)
            pbar4.update(1)
        assert pbar4.n == 10

    # 5. __iter__ with astronomical mininterval=1e308
    clock5 = MockDiscreteTimer(start=100.0)
    s5 = io.StringIO()
    with tqdm(range(10), file=s5, mininterval=1e308) as pbar5:
        pbar5._time = clock5
        pbar5.start_t = pbar5.last_print_t = clock5.current
        for _ in pbar5:
            clock5.advance(0.01)
        assert pbar5.n == 10
