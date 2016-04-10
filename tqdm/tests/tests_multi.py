import random

from tqdm import tqdm, trange, tqdm_multi
from tests_tqdm import _range, with_setup, pretest, posttest, StringIO, closing

@with_setup(pretest, posttest)
def test_multi():
    """ Test tqdm_multi with inherited tqdm instance"""
    class TestJob(tqdm):

        def __init__(self, task_num, **kwargs):
            super(TestJob, self).__init__(**kwargs)
            self.task_num = task_num

        def update(self):
            super(TestJob, self).update(self.task_num)

        def handle_result(self, **kwargs):
            if self.task_num == 5:
                raise NameError('No 5s allowed')
            else:
                return 'Success: {self.task_num}\n'.format(self=self)

        def success_callback(self, **kwargs):
            kwargs['out'].write(kwargs['result'])

        def failure_callback(self, **kwargs):
            kwargs['out'].write('Failed {self.task_num} with error: "{error}"\n'.format(
                self=self, error=kwargs['error'])
            )
            multi.register_job(self.restart_job())

        def restart_job(self):
            new_task_num = self.task_num * 10 + 2
            return TestJob(task_num=new_task_num, file=self.fp, desc=str(new_task_num), total=100)

    with closing(StringIO()) as our_file:
        multi = tqdm_multi()
        for __ in _range(10):
            task_num = random.randint(1, 10)
            job = TestJob(task_num=task_num, file=our_file, desc=str(task_num), total=100)
            multi.register_job(job)
        with closing(StringIO()) as output:
            multi.run(sleep_delay=.001, out=output)

@with_setup(pretest, posttest)
def iterable_test():
    """ Test tqdm_multi with tqdm from iterable"""
    with closing(StringIO()) as our_file:
        multi = tqdm_multi()
        for __ in _range(10):
            job = trange(1, 10, file=our_file)
            multi.register_job(job)
        multi.run(sleep_delay=.001)
