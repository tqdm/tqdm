import time

from ._tqdm import tqdm

"""
**NOTES**
    Issues:
        - When a Bar calls `close()`, it messes up other bars.
            (This is somewhat fixed with the clear and refresh)
        - Need to handle moving command line cursor to below bars
    Considerations:
        - fiure out best place to call run_callbacks() in non-multi context
        - this would work well with the print-message branch. The clear
            and refresh methods are from there as well.
        - How to handle async
        - Naming conventions?
        - Better way to handle task registry

    Here is a minimum example with inheritence (see tests/tests_multi.py for a
        more detailed example):
    ```
        class MiniTestJob(tqdm):

            def __init__(self, task_num, **kwargs):
                super(MiniTestJob, self).__init__(**kwargs)
                self.task_num = task_num

            def update(self):
                super(MiniTestJob, self).update(n=self.task_num)

        def mini_test():
            multi = tqdm_multi()
            for task_num in range(1, 10):
                job = MiniTestJob(task_num=task_num, desc=str(task_num), total=1000)
                multi.register_job(job)
            multi.run(sleep_delay=.001)
    ```
"""


class tqdm_multi(object):
    """
    A handler for running multiple progress bars simultaneously.
    Interacts with the tqdm_job wrapper which provides useful hooks
    that can be used to update the progress bars and return results
    dynamically.

    The user can create a class that inherits from tqdm_job to create a simple
    interface around a tqdm instance, and define their own methods for handling
    the update, and success/failure logic. The user can pass instances of these
    interfaces to tqdm_multi to handle iterating through this logic.

    See tests/tests_multi.py for an example
    """
    def __init__(self, jobs=[]):
        self.jobs = jobs

    def register_job(self, job):
        self.jobs.append(job)

    def run(self, sleep_delay=.25, **kwargs):
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
                    job.run_callbacks(multi=self, **kwargs)
                else:
                    time.sleep(sleep_delay)
        for job in self.jobs:
            job.close()

    def _incomplete_jobs(self):
        "returns a list of any progress bars that are still unfinished"
        return [job for job in self.jobs if not job._is_complete()]
