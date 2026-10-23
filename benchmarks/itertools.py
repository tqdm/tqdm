from tqdm.contrib.itertools import combinations_with_replacement


class CombinationsWithReplacement:
    """Time total inference without enumerating the combinations."""
    params = ([1, 2, 10], [10, 10000])
    param_names = ['n', 'r']

    def time_initialization(self, n, r):
        with combinations_with_replacement(range(n), r, disable=True):
            pass
