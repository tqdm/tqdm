from pytest import importorskip, mark

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


@mark.parametrize("status", [400, None])
def test_telegram_token_redacted(status, capsys, monkeypatch):
    """Test bot token (part of the API URL) is not printed on errors"""
    requests = importorskip("requests")
    from tqdm.contrib import telegram

    class Session:
        @staticmethod
        def post(url, **_):
            if status is None:
                raise requests.ConnectionError(f"Max retries exceeded with url: {url}")
            res = requests.Response()
            res.status_code, res.url, res._content = status, url, b'{"ok": false}'
            return res

    monkeypatch.setattr(telegram, "Session", Session)
    token = "123456:SECRET"
    assert telegram.TelegramIO(token, "0").message_id is None
    out = capsys.readouterr().out
    assert "<token>" in out
    assert token not in out
