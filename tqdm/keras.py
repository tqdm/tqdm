from __future__ import absolute_import
from .auto import tqdm as tqdm_auto
from copy import deepcopy
from keras.callbacks import Callback


class TqdmCallback(Callback):
    @staticmethod
    def bar2callback(bar, pop=None):
        def callback(_, logs=None):
            if logs:
                if pop:
                    logs = deepcopy(logs)
                    [logs.pop(i) for i in pop]
                bar.set_postfix(logs, refresh=False)
            bar.update()

        return callback

    def __init__(
        self,
        epochs,
        data_size=None,
        batch_size=None,
        verbose=1,
        tqdm_class=tqdm_auto,
    ):
        """
        Parameters
        ----------
        epochs  : int
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
        self.epoch_bar = tqdm_class(total=epochs, unit="epoch")
        self.on_epoch_end = self.bar2callback(self.epoch_bar)
        if data_size and batch_size:
            self.batches = batches = (data_size + batch_size - 1) // batch_size
        else:
            if verbose:
                print("W:missing batch and data size")
            verbose = 0
        self.verbose = verbose
        if verbose == 1:
            self.batch_bar = tqdm_class(
                total=batches, unit="batch", leave=False
            )
            self.on_batch_end = self.bar2callback(self.batch_bar, pop=["batch"])

    def on_epoch_begin(self, *_, **__):
        if self.verbose == 2:
            if hasattr(self, "batch_bar"):
                self.batch_bar.close()
            self.batch_bar = self.tqdm_class(
                total=self.batches, unit="batch", leave=True
            )
            self.on_batch_end = self.bar2callback(self.batch_bar, pop=["batch"])
        elif self.verbose == 1:
            self.batch_bar.reset()

    def on_train_end(self, *_, **__):
        if self.verbose:
            self.batch_bar.close()
        self.epoch_bar.close()
