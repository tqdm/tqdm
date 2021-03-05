# Benchmarks

These benchmarks serve two purposes:

1. Thorough performance tests against regression
    - `tqdm`
    - `tqdm(miniters=manually_optimised, smoothing=0)`
    - `no-progress` (empty loop without progress wrapper)
2. Compare `tqdm`'s speed to popular alternatives
    - [`rich.progress`](https://pypi.org/project/rich)
    - [`progressbar2`](https://pypi.org/project/progressbar2)
    - [`alive-progress`](https://pypi.org/project/alive-progress)

Performance graphs are available at <https://tqdm.github.io/tqdm>

## Running

These benchmarks are run automatically for all releases and pull requests.

To run locally:

- conda/pip install `virtualenv` and `asv`
- clone this repository
- run `asv --help` in the repository root (one directory above this file)
