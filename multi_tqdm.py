import time
from abc import ABCMeta, abstractmethod

from tqdm import tqdm

class MultiTQDM(object):
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
                        job.result_callback(**kwargs)
                    except:
                        job.failure_callback(**kwargs)
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

    def result_callback(self, **kwargs):
        pass

    def failure_callback(self, **kwargs):
        pass

    def _is_complete(self):
        return self.pbar.n >= self.pbar.total

class TestJob(TQDMJob):

    def __init__(self, task_num, **kwargs):
        super(TestJob, self).__init__(**kwargs)
        self.task_num = task_num

    def update(self):
        self.pbar.update(self.task_num)

    def result_callback(self, out):
        if self.task_num == 5:
            raise Exception
        else:
            out.write('Success: {self.task_num}\n'.format(self=self))

    def failure_callback(self, out):
        out.write('Failed: {self.task_num}\n'.format(self=self))

def get_test_jobs():
    for task_num in range(1, 10):
        job = TestJob(task_num=task_num, desc=str(task_num), total=1000)
        yield job

if __name__ == '__main__':
    multi = MultiTQDM()
    for job in get_test_jobs():
        multi.register_job(job)

    with open('results.txt', 'w') as out:
        multi.run(sleep_delay=.001, out=out)
