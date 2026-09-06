"""
Sends updates to mytqdm.app.

Usage:
>>> from tqdm.contrib.mytqdm import tqdm, trange
>>> for i in trange(10, api_key='{api_key}', title='{title}'):
...     ...

![link](https://mytqdm.app/)
"""
from os import getenv
from .utils_worker import MonoWorker

try:
    from requests import Session
except ImportError:
    raise ImportError("Please `pip install requests`")

from ..auto import tqdm as tqdm_auto

__author__ = {"github.com/padmalcom"}
__all__ = ['MyTqdm', 'mytqdmrange', 'tqdm', 'trange']

class MyTqdmIO(MonoWorker):
    """Non-blocking file-like IO using MyTqdm REST API."""
    PROGRESS_URL = "https://mytqdm.app/api/v1/p"

    def __init__(self, api_key, title):
        """Sending post requests to update a progress."""
        super().__init__()
        self.api_key = api_key
        self.title = title
        self.session = Session()

    def write(self, current, total):
        """Send current and total ints to mytqdm REST API."""
        headers = {
            "Authorization": f"X-API-Key {self.api_key}",
            "Accept": "application/json",
        }
        payload = {
            "title": self.title,
            "current": current,
            "total": total,
        }
        try:
            future = self.submit(
                self.session.post,
                self.PROGRESS_URL,
                headers=headers,
                json=payload)
        except Exception as e:
            tqdm_auto.write(str(e))
        else:
            return future

class MyTqdm(tqdm_auto):
    """
    Standard `tqdm.auto.tqdm` but also sends updates to a mytqdm.app.

    - enter your email adress on https://mytqdm.app to receive an api key.
    - put this private api key into the call below.
    - enter an optional title and use the link from the mail to open a
    widget or use the rest api to query your progress.
    >>> from tqdm.contrib.mytqdm import tqdm, trange
    >>> for i in tqdm(iterable, api_key='{api_key}', title='{title}'):
    ...     ...
    """

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        api_key  : str, required. mytqdm api key
            [default: ${MYTQDM_API_KEY}].
        title  : str, optional. A title to be displayed in the widget
            [default: ${MYTQDM_TITLE}].

        See `tqdm.auto.tqdm.__init__` for other parameters.
        """
        if not kwargs.get('disable'):
            kwargs = kwargs.copy()
            api_key = kwargs.pop('api_key', getenv("MYTQDM_API_KEY"))
            title = kwargs.pop('title', getenv("MYTQDM_TITLE"))
            self.mio = MyTqdmIO(api_key=api_key, title=title)
        super().__init__(*args, **kwargs)

    def display(self, msg=None, pos=None):
        super().display(msg=msg, pos=pos)
        self.mio.write(current=self.n, total=self.total)

def mytqdmrange(*args, **kwargs):
    """Shortcut for `tqdm.contrib.mytqdm.tqdm(range(*args), **kwargs)`."""
    return MyTqdm(range(*args), **kwargs)

# Aliases
tqdm = MyTqdm
trange = mytqdmrange
