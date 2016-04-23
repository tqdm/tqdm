import time

from ._tqdm import tqdm

"""
**NOTES**
    def mini_test():
        multi = tqdm_multi()
        for task_num in range(1, 10):
            job = tqdm(desc=str(task_num), total=1000)
            multi.register_job(job)
        multi.run(sleep_delay=.001)
    ```
"""


class tqdm_multi(object):
    """
    A handler for running multiple progress bars simultaneously.

    See tests/tests_multi.py for an example
    """
    def __init__(self, jobs=[], **kwargs):
        self.jobs = jobs
        if jobs:
            for job in jobs:
                self.register_job(job)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def register_job(self, job):
        self.jobs.append(job)
        job.multi = self

    def run(self, sleep_delay=.25):
        """
        run() handles the iteration aspect of tqdm_multi. `sleep_delay` is the
        number of seconds to wait between each update() for rate limiting purposes
        The user can also pass any number of kwargs to this function which are passed
        through to handle_result(), success_callback(), and failure_callback().

        See tqdm_job documentation for descriptions of how these methods
        can be used and customized.
        """
        while self._incomplete_jobs():
            for job in self._incomplete_jobs():
                job.update()
                if job._is_complete():
                    job.close()
                else:
                    time.sleep(sleep_delay)

    def _incomplete_jobs(self):
        "returns a list of any progress bars that are still unfinished"
        return [job for job in self.jobs if not job._is_complete()]
