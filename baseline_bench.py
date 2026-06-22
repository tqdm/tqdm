"""Baseline benchmark for tqdm optimization lab.
Measures tqdm overhead with lightweight per-iteration work.
"""
import statistics
import sys
import time

import tqdm as tqdm_mod
from tqdm import tqdm

# Lightweight per-iteration work to simulate real usage (not just empty loop)
WORK = lambda x: x ** 0.5

def bench(iterable, wrapper, name, trials=5):
    """Run `trials` times and return (mean, stdev) in seconds."""
    times = []
    for _ in range(trials):
        t0 = time.perf_counter()
        for item in wrapper(iterable):
            WORK(item)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    mean = statistics.mean(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0
    note = "*SAME" if stdev == 0 else f"±{stdev*1000:.2f}ms"
    print(f"  {name:<40s} {mean:8.4f}s ({note})")
    return mean

def main():
    print("tqdm version:", tqdm_mod.__version__)
    print("python:      ", sys.version.split()[0])
    print()

    scenarios = [
        ("light  (500K iter, ~1µs each)", 500_000,   None),
        ("medium (1M iter, ~1µs each)",  1_000_000,  None),
        ("heavy  (3M iter, ~1µs each)",  3_000_000,  None),
    ]

    for label, n, _ in scenarios:
        print(f"{'='*65}")
        print(f" {label}")
        print(f"{'='*65}")
        data = list(range(n))

        raw = bench(data, lambda x: x, "raw (no progress)", trials=3)
        td  = bench(data, tqdm, "tqdm (default)", trials=3)

        overhead_pct = ((td - raw) / raw) * 100
        print(f"  {'tqdm overhead:':40s} {overhead_pct:+.2f}%")
        print()

    print(f"{'='*65}")
    print(" BASELINE RECORDED")
    print(f"{'='*65}")
    print(f"  tqdm:  {tqdm_mod.__version__}")
    print(f"  python: {sys.version}")

if __name__ == "__main__":
    main()
