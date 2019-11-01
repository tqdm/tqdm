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

    def __init__(self, epochs, data_size=None, batch_size=None, verbose=1,
                 tqdm_class=tqdm_auto):
        """
        verbose  : 0=epoch, 1=temp batch, 2=batch
        """
        self.tqdm_class = tqdm_class
        self.te = tqdm_class(total=epochs, unit='epoch')
        self.on_epoch_end = self.bar2callback(self.te)
        if data_size and batch_size:
            self.batches = batches = (
                data_size + batch_size - 1) // batch_size
        else:
            if verbose:
                print("W:missing batch and data size")
            verbose = 0
        self.verbose = verbose
        if verbose == 1:
            self.tb = tqdm_class(total=batches, unit='batch', leave=False)
            self.on_batch_end = self.bar2callback(self.tb, ['batch'])

    def on_epoch_begin(self, *_, **__):
        if self.verbose == 2:
            if hasattr(self, 'tb'):
                self.tb.close()
            self.tb = self.tqdm_class(
                total=self.batches, unit='batch', leave=True)
            self.on_batch_end = self.bar2callback(self.tb, ['batch'])
        elif self.verbose == 1:
            self.tb.reset()

    def on_train_end(self, *_, **__):
        if self.verbose:
            self.tb.close()
        self.te.close()
