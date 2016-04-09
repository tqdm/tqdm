import time

from ._tqdm import tqdm

"""
**NOTES**
    Issues:
        - When a Bar calls `close()`, it messes up other bars.
            (This is somewhat fixed with the clear and refresh)
        - Need to handle moving command line cursor to below bars
    Considerations:
        - this would work well with the print-message branch. The clear
            and refresh methods are from there as well.
        - How to handle async
        - Naming conventions?
        - Better way to handle task registry
"""


class multi_tqdm(object):
    def __init__(self, jobs=[]):
        self.jobs = jobs

    def register_job(self, job):
        self.jobs.append(job)

    def run(self, sleep_delay=.25, **kwargs):
        while self._incomplete_jobs():
            for job in self._incomplete_jobs():
                job.update()
                if job._is_complete():
                    try:
                        result = job.handle_result(**kwargs)
                        job.success_callback(multi=self, result=result, **kwargs)
                    except Exception as error:
                        job.failure_callback(multi=self, error=error, **kwargs)
                    finally:
                        for inst in job.pbar._instances:
                            inst.clear()
                            inst.refresh()
                else:
                    time.sleep(sleep_delay)

    def _incomplete_jobs(self):
        return [job for job in self.jobs if not job._is_complete()]

class tqdm_job(object):
    _positions = 0

    def __init__(self, **kwargs):
        self.position = tqdm_job._positions
        self.pbar = tqdm(position=self.position, **kwargs)
        tqdm_job._positions += 1

    def __str__(self):
        return str(self.position)

    def update(self):
        self.pbar.update()

    def handle_result(self, **kwargs):
        pass

    def success_callback(self, multi, result, **kwargs):
        pass

    def failure_callback(self, multi, error, **kwargs):
        pass

    def _is_complete(self):
        return self.pbar.n >= self.pbar.total
