from tqdm import tqdm
from tqdm.keras import TqdmCallback
from tests_tqdm import with_setup, pretest, posttest, SkipTest, StringIO, closing


@with_setup(pretest, posttest)
def test_keras():
    """Test tqdm.keras.TqdmCallback"""
    try:
        import numpy as np
        import keras as K
    except ImportError:
        raise SkipTest

    # 1D autoencoder
    dtype = np.float32
    model = K.models.Sequential(
        [K.layers.InputLayer((1, 1), dtype=dtype), K.layers.Conv1D(1, 1)]
    )
    model.compile("adam", "mse")
    x = np.random.rand(100, 1, 1).astype(dtype)
    batch_size = 10
    epochs = 5

    with closing(StringIO()) as our_file:

        class Tqdm(tqdm):
            """redirected I/O class"""

            def __init__(self, *a, **k):
                k.setdefault("file", our_file)
                super(Tqdm, self).__init__(*a, **k)

        # just epoch (no batch) progress
        model.fit(
            x,
            x,
            epochs=epochs,
            batch_size=batch_size,
            verbose=False,
            callbacks=[
                TqdmCallback(
                    epochs,
                    data_size=len(x),
                    batch_size=batch_size,
                    verbose=0,
                    tqdm_class=Tqdm,
                )
            ],
        )
        res = our_file.getvalue()
        assert res.count("100%") == 1
        assert "{epochs}/{epochs}".format(epochs=epochs) in res

        # full (epoch and batch) progress
        our_file.seek(0)
        our_file.truncate()
        model.fit(
            x,
            x,
            epochs=epochs,
            batch_size=batch_size,
            verbose=False,
            callbacks=[
                TqdmCallback(
                    epochs,
                    data_size=len(x),
                    batch_size=batch_size,
                    verbose=2,
                    tqdm_class=Tqdm,
                )
            ],
        )
        res = our_file.getvalue()
        assert res.count("100%") >= epochs + 1
        assert "{epochs}/{epochs}".format(epochs=epochs) in res
