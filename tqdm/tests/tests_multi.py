import random

from tqdm import tqdm, trange, tqdm_multi
from tests_tqdm import _range, with_setup, pretest, posttest, StringIO, closing

@with_setup(pretest, posttest)
def full_multi_test():
    """Test tqdm_multi full feature test"""
    class TestJob(tqdm):

        def __init__(self, task_num, **kwargs):
            super(TestJob, self).__init__(**kwargs)
            self.task_num = task_num

        def update(self):
            super(TestJob, self).update(self.task_num)

        def handle_result(self):
            if self.task_num == 5:
                raise NameError('No 5s allowed')
            else:
                return 'Success: {self.task_num}\n'.format(self=self)

        def success_callback(self, result):
            self.multi.out.write(result)

        def failure_callback(self, error):
            self.multi.out.write('Failed {self.task_num} with error: "{error}"\n'.format(
                self=self, error=error)
            )
            self.multi.register_job(self.restart_job())

        def restart_job(self):
            new_task_num = self.task_num * 10 + 2
            return TestJob(task_num=new_task_num, file=self.fp, desc=str(new_task_num), total=1000)

    with closing(StringIO()) as out:
        multi = tqdm_multi(out=out)
        with closing(StringIO()) as our_file:
            for task_num in range(1, 10):
                task_num = random.randint(1, 10)
                job = TestJob(task_num=task_num, desc=str(task_num), total=100, file=our_file)
                multi.register_job(job)
            multi.run(sleep_delay=.001)

@with_setup(pretest, posttest)
def mini_test():
    """Test tqdm_multi with extra attribute"""
    class MiniTestJob(tqdm):

        def __init__(self, task_num, **kwargs):
            super(MiniTestJob, self).__init__(**kwargs)
            self.task_num = task_num

        def update(self):
            super(MiniTestJob, self).update(n=self.task_num)

    multi = tqdm_multi()
    with closing(StringIO()) as our_file:
        for task_num in _range(1, 5):
            job = MiniTestJob(task_num=task_num, desc=str(task_num), total=100, file=our_file)
            multi.register_job(job)
        multi.run(sleep_delay=.001)

@with_setup(pretest, posttest)
def iterable_test():
    """Test tqdm_multi with trange"""
    multi = tqdm_multi()
    with closing(StringIO()) as our_file:
        for __ in _range(1, 5):
            job = trange(1, 10, file=our_file)
            multi.register_job(job)
        multi.run(sleep_delay=.001)

@with_setup(pretest, posttest)
def iterable_with_inheritence_test():
    """Test tqdm_multi iterable test with handle_result only"""
    class CustomIterable(tqdm):

        def __init__(self, *args, **kwargs):
            super(CustomIterable, self).__init__(*args, **kwargs)

        def handle_result(self):
            self.multi.out.write('success\n')

    with closing(StringIO()) as out:
        multi = tqdm_multi(out=out)
        with closing(StringIO()) as our_file:
            for __ in range(1, 5):
                job = CustomIterable(range(1, 100), file=our_file)
                multi.register_job(job)
            multi.run(sleep_delay=.001)

@with_setup(pretest, posttest)
def callback_only_test():
    """test result handling on finish with no multi"""
    class callback_tqdm(tqdm):

        def __init__(self, *args, **kwargs):
            super(callback_tqdm, self).__init__(*args, **kwargs)

        def handle_result(arg):
            rand = random.randint(1, 10)
            if rand < 5:
                raise NameError('{0} is Less than 5!'.format(rand))
            else:
                return '{0} is At Least 5!'.format(rand)

        def success_callback(self, result):
            print('Success!', result)

        def failure_callback(self, error):
            print('Failed!', error)

    for i in callback_tqdm(range(1, 10)):
        print(i)
