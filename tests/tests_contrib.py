from importlib import import_module

from pytest import importorskip, mark, raises

from tqdm import tqdm
from tqdm.contrib import tenumerate, tmap, tzip


@mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_enumerate(tqdm_kwargs, caperr):
    a = range(9)
    assert list(tenumerate(a, **tqdm_kwargs)) == list(enumerate(a))
    assert list(tenumerate(a, 42, **tqdm_kwargs)) == list(enumerate(a, 42))
    caperr()

    _ = list(tenumerate(iter(a), **tqdm_kwargs))
    assert "100%" not in caperr()
    _ = list(tenumerate(iter(a), total=len(a), **tqdm_kwargs))
    assert "100%" in caperr()


def test_enumerate_numpy(caperr):
    np = importorskip("numpy")
    a = np.random.random((42, 7))
    assert list(tenumerate(a)) == list(np.ndenumerate(a))
    assert "100%" in caperr()


@mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_zip(tqdm_kwargs):
    a = range(9)
    b = [i + 1 for i in a]
    gen = tzip(a, b, **tqdm_kwargs)
    assert gen != list(zip(a, b))
    assert list(gen) == list(zip(a, b))


@mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_map(tqdm_kwargs):
    a = range(9)
    b = [i + 1 for i in a]
    gen = tmap(lambda x: x + 1, a, **tqdm_kwargs)
    assert gen != b
    assert list(gen) == b


@mark.parametrize("module_name,class_name", [
    ("tqdm.contrib.discord", "DiscordIO"),
    ("tqdm.contrib.telegram", "TelegramIO"),
])
def test_contrib_connection_error(monkeypatch, module_name, class_name):
    """Connection errors must not be masked by UnboundLocalError (tqdm#1812)."""
    requests = importorskip("requests")
    io_class = getattr(import_module(module_name), class_name)
    message = f"{class_name} connection failed"

    def post(*args, **kwargs):
        raise requests.exceptions.ConnectionError(message)

    monkeypatch.setattr(requests.Session, "post", post)
    with raises(requests.exceptions.ConnectionError, match=message):
        io_class("token", "id")
