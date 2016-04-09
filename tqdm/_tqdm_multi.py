import time

from ._tqdm import tqdm

"""
**NOTES**
    I'm really not sure if this is the best way to go about things. The whole
    wrapper/interface idea still feels a little clunky. There is probably a
    better way to build all of this functionality into tqdm properly. Definitely
    Open to feedback on better ways to do any/all of this.
    Issues:
        - Need to test if it can handle being passed iterables
        - When a Bar calls `close()`, it messes up other bars.
            (This is somewhat fixed with the clear and refresh)
        - Need to handle moving command line cursor to below bars
        - Needs compatibility testing
    Considerations:
        - this would work well with the print-message branch. The clear
            and refresh methods are from there as well.
        - How to handle async
        - Naming conventions?
        - Better way to handle task registry

    Here is a minimum example (see tests/tests_multi.py for a more detailed example):
    ```
        from tqdm import multi_tqdm, tqdm_job

        class MiniTestJob(tqdm_job):

            def __init__(self, task_num, **kwargs):
                super(MiniTestJob, self).__init__(**kwargs)
                self.task_num = task_num

            def update(self):
                self.pbar.update(n=self.task_num)

        def mini_test():
            multi = multi_tqdm()
            for task_num in range(1, 10):
                job = MiniTestJob(task_num=task_num, desc=str(task_num), total=1000)
                multi.register_job(job)
            multi.run(sleep_delay=.001)
    ```
"""


class multi_tqdm(object):
    """
    A handler for running multiple progress bars simultaneously.
    Interacts with the tqdm_job wrapper which provides useful hooks
    that can be used to update the progress bars and return results
    dynamically.

    The user can create a class that inherits from tqdm_job to create a simple
    interface around a tqdm instance, and define their own methods for handling
    the update, and success/failure logic. The user can pass instances of these
    interfaces to multi_tqdm to handle iterating through this logic.

    See tests/tests_multi.py for an example
    """
    def __init__(self, jobs=[]):
        self.jobs = jobs

    def register_job(self, job):
        self.jobs.append(job)

    def run(self, sleep_delay=.25, **kwargs):
        """
        run() handles the iteration aspect of multi_tqdm. `sleep_delay` is the
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
        "returns a list of any progress bars that are still unfinished"
        return [job for job in self.jobs if not job._is_complete()]

class tqdm_job(object):
    """
    An abstract class to use as a wrapper for tasks to be handled
    by a multi_tqdm instance. Each class that inherits from this class
    can implement any of the following methods detailed below.
    """

    _positions = 0

    def __init__(self, **kwargs):
        """
        (Needs refactoring) This class has a counter of the number of instances
        of any user made classes that inherit from it. `position` is set from This
        counter. Any other kwargs here are passed directly to the tqdm instance which
        is created as `self.pbar`
        """
        self.position = tqdm_job._positions
        self.pbar = tqdm(position=self.position, **kwargs)
        tqdm_job._positions += 1

    def __str__(self):
        return str(self.position)

    def update(self):
        """
        The class can manually update the tqdm instance each iteration here.
        [default: tqdm.update()]
        """
        self.pbar.update()

    def handle_result(self, **kwargs):
        """
        Called when the tqdm instance is finished. Can return data which will be
        handled by the success_callback() as `result` or raise an exception which
        will be passed to the failure_callback() as `error`. [default: pass]
        """
        pass

    def success_callback(self, multi, result, **kwargs):
        """
        Called after handle_result() has finsihed without an exception. Has
        access to the multi_tqdm instance as `multi`, and any results returned
        from handle_result() as `result`. Also has access to any kwargs a user
        passed in to multi_tqdm.run(). [default: pass]
        """
        pass

    def failure_callback(self, multi, error, **kwargs):
        """
        Called after handle_result() raises an exception. Has access to the
        multi_tqdm instance as `multi`, and the error message returned from
        handle_result() as `error`. Also has access to any kwargs a user passed
        in to multi_tqdm.run(). [default: pass]
        """
        pass

    def _is_complete(self):
        """(Needs refactoring) A way to see if a progress bar has finished"""
        return self.pbar.n >= self.pbar.total
