"""
Tests for `tqdm.contrib`.
"""
import pytest

from tqdm import tqdm
from tqdm.contrib import tenumerate, tmap, tzip

from .tests_tqdm import StringIO, closing, importorskip


def incr(x):
    """Dummy function"""
    return x + 1


@pytest.mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_enumerate(tqdm_kwargs):
    """Test contrib.tenumerate"""
    with closing(StringIO()) as our_file:
        a = range(9)
        assert list(tenumerate(a, file=our_file, **tqdm_kwargs)) == list(enumerate(a))
        assert list(tenumerate(a, 42, file=our_file, **tqdm_kwargs)) == list(
            enumerate(a, 42)
        )
    with closing(StringIO()) as our_file:
        _ = list(tenumerate(iter(a), file=our_file, **tqdm_kwargs))
        assert "100%" not in our_file.getvalue()
    with closing(StringIO()) as our_file:
        _ = list(tenumerate(iter(a), file=our_file, total=len(a), **tqdm_kwargs))
        assert "100%" in our_file.getvalue()


def test_enumerate_numpy():
    """Test contrib.tenumerate(numpy.ndarray)"""
    np = importorskip("numpy")
    with closing(StringIO()) as our_file:
        a = np.random.random((42, 7))
        assert list(tenumerate(a, file=our_file)) == list(np.ndenumerate(a))


@pytest.mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_zip(tqdm_kwargs):
    """Test contrib.tzip"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        gen = tzip(a, b, file=our_file, **tqdm_kwargs)
        assert gen != list(zip(a, b))
        assert list(gen) == list(zip(a, b))


@pytest.mark.parametrize("tqdm_kwargs", [{}, {"tqdm_class": tqdm}])
def test_map(tqdm_kwargs):
    """Test contrib.tmap"""
    with closing(StringIO()) as our_file:
        a = range(9)
        b = [i + 1 for i in a]
        gen = tmap(lambda x: x + 1, a, file=our_file, **tqdm_kwargs)
        assert gen != b
        assert list(gen) == b


def test_discord_network_error(monkeypatch):
    """Test DiscordIO handles network error without raising UnboundLocalError (#1812)"""
    requests = importorskip("requests")
    from tqdm.contrib.discord import DiscordIO

    def mock_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Connection refused")

    monkeypatch.setattr(requests.Session, "post", mock_post)
    dio = DiscordIO("TOKEN", "CHANNEL")
    assert dio.message_id is None


def test_telegram_network_error(monkeypatch):
    """Test TelegramIO handles network error without raising UnboundLocalError (#1812)"""
    requests = importorskip("requests")
    from tqdm.contrib.telegram import TelegramIO

    def mock_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Connection refused")

    monkeypatch.setattr(requests.Session, "post", mock_post)
    tgio = TelegramIO("TOKEN", "CHANNEL")
    assert tgio.message_id is None


def test_discord_rate_limit(monkeypatch):
    """Test DiscordIO warns on 429 rate limit"""
    requests = importorskip("requests")
    from tqdm.contrib.discord import DiscordIO
    from tqdm.std import TqdmWarning

    class MockResponse:
        status_code = 429

        def json(self):
            return {}

        def raise_for_status(self):
            raise requests.exceptions.HTTPError(response=self)

    monkeypatch.setattr(
        requests.Session, "post", lambda *args, **kwargs: MockResponse()
    )
    with pytest.warns(TqdmWarning, match="Creation rate limit"):
        dio = DiscordIO("TOKEN", "CHANNEL")
        assert dio.message_id is None


def test_telegram_rate_limit(monkeypatch):
    """Test TelegramIO warns on 429 rate limit"""
    requests = importorskip("requests")
    from tqdm.contrib.telegram import TelegramIO
    from tqdm.std import TqdmWarning

    class MockResponse:
        status_code = 429

        def json(self):
            return {}

        def raise_for_status(self):
            raise requests.exceptions.HTTPError(response=self)

    monkeypatch.setattr(
        requests.Session, "post", lambda *args, **kwargs: MockResponse()
    )
    with pytest.warns(TqdmWarning, match="Creation rate limit"):
        tgio = TelegramIO("TOKEN", "CHANNEL")
        assert tgio.message_id is None
