from __future__ import absolute_import
from .auto import tqdm as tqdm_auto
from copy import deepcopy
from keras.callbacks import Callback


class TqdmCallback(Callback):
    @staticmethod
    def bar2callback(bar, pop=None, delta=(lambda logs: 1)):
        def callback(_, logs=None):
            if logs:
                if pop:
                    logs = deepcopy(logs)
                    [logs.pop(i) for i in pop]
                bar.set_postfix(logs, refresh=False)
            bar.update(delta(logs))

        return callback

    def __init__(self, epochs=None, data_size=None, batch_size=None, verbose=1,
                 tqdm_class=tqdm_auto):
        """
        Parameters
        ----------
        epochs  : int, optional
        data_size  : int, optional
            Number of training pairs.
        batch_size  : int, optional
            Number of training pairs per batch.
        verbose  : int
            0: epoch, 1: batch (transient), 2: batch. [default: 1].
            Will be set to `0` unless both `data_size` and `batch_size`
            are given.
        tqdm_class : optional
            `tqdm` class to use for bars [default: `tqdm.auto.tqdm`].
        """
        self.tqdm_class = tqdm_class
        self.epoch_bar = tqdm_class(total=epochs, unit='epoch')
        self.on_epoch_end = self.bar2callback(self.epoch_bar)
        if data_size and batch_size:
            self.batches = batches = (data_size + batch_size - 1) // batch_size
        else:
            self.batches = batches = None
        self.verbose = verbose
        if verbose == 1:
            self.batch_bar = tqdm_class(total=batches, unit='batch',
                                        leave=False)
            self.on_batch_end = self.bar2callback(
                self.batch_bar,
                pop=['batch'],
                delta=lambda logs: logs.get('size', 1))

    def on_train_begin(self, *_, **__):
        params = self.params.get
        auto_total = params('epochs', params('nb_epoch', None))
        if auto_total:
            self.epoch_bar.total = auto_total

    def on_epoch_begin(self, *_, **__):
        if self.verbose:
            params = self.params.get
            auto_total = params(
                'samples', params('nb_sample', params('steps', None)))
            if self.verbose == 2:
                if hasattr(self, 'batch_bar'):
                    self.batch_bar.close()
                self.batch_bar = self.tqdm_class(
                    total=auto_total or self.batches, unit='batch', leave=True)
                self.on_batch_end = self.bar2callback(
                    self.batch_bar,
                    pop=['batch'],
                    delta=lambda logs: logs.get('size', 1))
            elif self.verbose == 1:
                self.batch_bar.reset(total=auto_total or self.batches)
            else:
                raise KeyError('Unknown verbosity')

    def on_train_end(self, *_, **__):
        if self.verbose:
            self.batch_bar.close()
        self.epoch_bar.close()
