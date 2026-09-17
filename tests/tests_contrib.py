from pytest import importorskip, mark, warns

from tqdm import tqdm
from tqdm.contrib import tenumerate, tmap, tzip
from tqdm.std import TqdmWarning


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


def _bot_io(name, session_cls, monkeypatch):
    """`DiscordIO`/`TelegramIO` with `requests.Session` replaced by `session_cls`"""
    module = importorskip(f"tqdm.contrib.{name}")
    monkeypatch.setattr(module, "Session", session_cls)
    return getattr(module, f"{name.capitalize()}IO")("TOKEN", "CHAT")


@mark.parametrize("name", ["discord", "telegram"])
def test_bot_connection_error(name, monkeypatch, capsys):
    """Original error is reported when the creation request never completes"""
    requests = importorskip("requests")

    class Session:
        def post(self, *_, **__):
            raise requests.ConnectionError("connection refused")

    assert _bot_io(name, Session, monkeypatch).message_id is None
    assert "connection refused" in capsys.readouterr().out


@mark.parametrize("name", ["discord", "telegram"])
def test_bot_rate_limit(name, monkeypatch):
    """Creation rate limit (HTTP 429) is reported as a warning"""
    requests = importorskip("requests")

    class Response:
        status_code = 429

        def raise_for_status(self):
            raise requests.HTTPError("429 Too Many Requests", response=self)

    class Session:
        def post(self, *_, **__):
            return Response()

    with warns(TqdmWarning, match="rate limit"):
        assert _bot_io(name, Session, monkeypatch).message_id is None
