from dask.callbacks import Callback
from ._tqdm import tqdm


class ProgressBar(Callback):
    def __init__(self, tclass=tqdm, *targs, **tkwargs):
        """
        Progress bar class to use with dask.
        
        Parameters
        ----------
        tclass  : class or instance of tqdm (e.g. tqdm_notebook())
        targs, tkwargs  : arguments for the tqdm instance
        """
        if not isinstance(tclass, type):
            tclass = type(class)
        self._tclass = tclass
        self._targs = targs
        self._tkwargs = tkwargs

    def _start_state(self, dsk, state):
        self._tqdm = self.tclass(total=sum(len(state[k]) for k in ['ready', 'waiting', 'running', 'finished']),
                                 *self.targs, **self.tkwargs)

    def _posttask(self, key, result, dsk, state, worker_id):
        self._tqdm.update(1)

    def _finish(self, dsk, state, errored):
        self._tqdm.close()
