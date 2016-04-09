import time
from abc import ABCMeta, abstractmethod

from ._tqdm import tqdm

"""
**NOTES**
    Issues:
        - **kwargs passing doesn't work if the user doesn't take the parameters
          in each of their defined functions.
        -
    Considerations:
        - How to handle async
        - Naming conventions?

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
                        job.success_callback(result, **kwargs)
                    except:
                        job.failure_callback(result, **kwargs)
                    finally:
                        job.pbar.close()
                else:
                    time.sleep(sleep_delay)

    def _incomplete_jobs(self):
        return [job for job in self.jobs if not job._is_complete()]

class tqdm_job(object):
    _positions = 0

    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        self.position = tqdm_job._positions
        self.pbar = tqdm(position=self.position, **kwargs)
        tqdm_job._positions += 1

    def __str__(self):
        return str(self.position)

    @abstractmethod
    def update(self):
        pass

    def handle_result(self, **kwargs):
        pass

    def success_callback(self, **kwargs):
        pass

    def failure_callback(self, **kwargs):
        pass

    def _is_complete(self):
        return self.pbar.n >= self.pbar.total
