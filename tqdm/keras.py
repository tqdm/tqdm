"""Submodule for Keras callbacks."""

from copy import copy
from functools import partial

from .auto import tqdm as tqdm_auto

try:
    import keras
except (ImportError, AttributeError) as keras_import_exception:
    try:
        from tensorflow import keras
    except ImportError as tensorflow_import_exception:
        raise ImportError(
            "Could not import `keras` or `tensorflow.keras`."
        ) from tensorflow_import_exception
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ["TqdmCallback"]


class TqdmCallback(keras.callbacks.Callback):
    """Keras callback for epoch and batch progress."""

    @staticmethod
    def bar2callback(tqdm_instance, pop=None, delta=(lambda logs: 1), metrics=None):
        """Converts a `tqdm` bar to a Keras callback.

        Parameters
        ----------
        tqdm_instance  : `tqdm` instance
        pop  : list, optional
            List of keys to remove from logs.
        delta  : callable, optional
            Function to calculate the delta from logs.
        metrics  : list, optional
            List of metrics to display.
        """

        def callback(_, logs=None):
            n = delta(logs)
            if logs:
                if pop:
                    logs = copy(logs)
                    _ = [logs.pop(i, 0) for i in pop]
                if metrics:
                    logs = copy(logs)
                    logs = {
                        metric: logs[metric] for metric in metrics if metric in logs
                    }
                tqdm_instance.set_postfix(logs, refresh=False)
            tqdm_instance.update(n)

        return callback

    def __init__(
        self,
        epochs=None,
        data_size=None,
        batch_size=None,
        verbose=1,
        metrics=None,
        tqdm_class=tqdm_auto,
        **tqdm_kwargs,
    ):
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
        metrics  : list, optional
            List of metrics to display
        tqdm_class  : optional
            `tqdm` class to use for bars [default: `tqdm.auto.tqdm`].
        tqdm_kwargs  : optional
            Any other arguments used for all bars.
        """
        if tqdm_kwargs:
            tqdm_class = partial(tqdm_class, **tqdm_kwargs)
        self.tqdm_class = tqdm_class
        self.epoch_bar = tqdm_class(total=epochs, unit="epoch")
        self.on_epoch_end = self.bar2callback(self.epoch_bar, metrics=metrics)
        if data_size and batch_size:
            self.batches = batches = (data_size + batch_size - 1) // batch_size
        else:
            self.batches = batches = None
        self.verbose = verbose
        self.metrics = metrics
        if verbose == 1:
            self.batch_bar = tqdm_class(total=batches, unit="batch", leave=False)
            self.on_batch_end = self.bar2callback(
                self.batch_bar,
                pop=["batch", "size"],
                delta=lambda logs: logs.get("size", 1),
                metrics=self.metrics,
            )

    def on_train_begin(self, *_, **__):
        """Called at the beginning of training to reset the bars."""
        params = self.params.get
        auto_total = params("epochs", params("nb_epoch", None))
        if auto_total is not None and auto_total != self.epoch_bar.total:
            self.epoch_bar.reset(total=auto_total)

    def on_epoch_begin(self, epoch, *_, **__):
        """Called at the beginning of each epoch to reset the bars."""
        if self.epoch_bar.n < epoch:
            ebar = self.epoch_bar
            ebar.n = ebar.last_print_n = ebar.initial = epoch
        if self.verbose:
            params = self.params.get
            total = (
                params("samples", params("nb_sample", params("steps", None)))
                or self.batches
            )
            if self.verbose == 2:
                if hasattr(self, "batch_bar"):
                    self.batch_bar.close()
                self.batch_bar = self.tqdm_class(
                    total=total,
                    unit="batch",
                    leave=True,
                    unit_scale=1 / (params("batch_size", 1) or 1),
                )
                self.on_batch_end = self.bar2callback(
                    self.batch_bar,
                    pop=["batch", "size"],
                    delta=lambda logs: logs.get("size", 1),
                    metrics=self.metrics,
                )
            elif self.verbose == 1:
                self.batch_bar.unit_scale = 1 / (params("batch_size", 1) or 1)
                self.batch_bar.reset(total=total)
            else:
                raise KeyError("Unknown verbosity")

    def on_train_end(self, *_, **__):
        """Called at the end of training to close the bars."""
        if hasattr(self, "batch_bar"):
            self.batch_bar.close()
        self.epoch_bar.close()

    def display(self):
        """Displays in the current cell in Notebooks."""
        container = getattr(self.epoch_bar, "container", None)
        if container is None:
            return
        from tqdm.notebook import display  # pylint: disable=import-outside-toplevel

        display(container)
        batch_bar = getattr(self, "batch_bar", None)
        if batch_bar is not None:
            display(batch_bar.container)

    @staticmethod
    def _implements_train_batch_hooks():
        return True

    @staticmethod
    def _implements_test_batch_hooks():
        return True

    @staticmethod
    def _implements_predict_batch_hooks():
        return True
