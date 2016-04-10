import random

from tqdm import tqdm, multi_tqdm, tqdm_job
from tests_tqdm import with_setup, pretest, posttest, StringIO, closing

@with_setup(pretest, posttest)
def test_multi():
    """ Test multi_tqdm with test tqdm_job """
    class TestJob(tqdm_job):

        def __init__(self, task_num, **kwargs):
            super(TestJob, self).__init__(**kwargs)
            self.task_num = task_num

        def update(self):
            super(TestJob, self).update(self.task_num)

        def handle_result(self, out):
            if self.task_num == 5:
                raise NameError('No 5s allowed')
            else:
                return 'Success: {self.task_num}\n'.format(self=self)

        def success_callback(self, **kwargs):
            kwargs['out'].write(kwargs['result'])
            self.close()

        def failure_callback(self, **kwargs):
            kwargs['out'].write('Failed {self.task_num} with error: "{error}"\n'.format(
                self=self, error=kwargs['error'])
            )
            multi.register_job(self.restart_job())
            self.close()

        def restart_job(self):
            new_task_num = self.task_num * 10 + 2
            return TestJob(task_num=new_task_num, file=self.fp, desc=str(new_task_num), total=100)

    with closing(StringIO()) as our_file:
        multi = multi_tqdm()
        for __ in range(1, 10):
            task_num = random.randint(1, 10)
            job = TestJob(task_num=task_num, file=our_file, desc=str(task_num), total=100)
            multi.register_job(job)
        with closing(StringIO()) as output:
            multi.run(sleep_delay=.001, out=output)
