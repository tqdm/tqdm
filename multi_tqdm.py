import time
import pudb
# import sys
from abc import ABCMeta, abstractmethod

from tqdm import tqdm

class MultiTQDM(object):
    def __init__(self, jobs=[]):
        self.jobs = jobs

    def register_job(self, job):
        self.jobs.append(job)

    def run(self, sleep_delay=.25):
        while self._incomplete_jobs():
            for job in self._incomplete_jobs():
                job.update()
                if job._is_complete():
                    try:
                        yield job.result_callback()
                    except:
                        yield job.failure_callback()
                    finally:
                        job.pbar.close()
                else:
                    time.sleep(sleep_delay)

    def _incomplete_jobs(self):
        return [job for job in self.jobs if not job._is_complete()]

class TQDMJob(object):
    _positions = 0

    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        self.position = TQDMJob._positions
        self.pbar = tqdm(position=self.position, **kwargs)
        TQDMJob._positions += 1

    def __str__(self):
        return str(self.position)

    @abstractmethod
    def update(self):
        pass

    def result_callback(self):
        "returns: result callback"
        pass

    def failure_callback(self):
        "returns: failure callback"
        pass

    def _is_complete(self):
        return self.pbar.n >= self.pbar.total

    def _n_remaining(self):
        return self.pbar.total - self.pbar.n

class TestJob(TQDMJob):

    def __init__(self, task, **kwargs):
        super(TestJob, self).__init__(**kwargs)
        self.task = task

    def update(self):
        update_amt = self._n_remaining() if self._n_remaining() < self.task else self.task
        self.pbar.update(update_amt)

    def result_callback(self):
        if self.task == 5:
            raise Exception
        else:
            return 'Success: {self.task}\n'.format(self=self)

    def failure_callback(self):
        return 'Failed: {self.task}\n'.format(self=self)

def get_test_jobs():
    for task_id in range(1, 10):
        job = TestJob(task=task_id, desc=str(task_id), total=1000)
        yield job

if __name__ == '__main__':
    multi = MultiTQDM()
    for job in get_test_jobs():
        multi.register_job(job)

    # pudb.set_trace()
    with open('results.txt', 'w') as out:
        for result in multi.run(.001):
            if result:
                out.write(result)
