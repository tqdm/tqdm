"""
Sends updates to mytqdm.app.

Usage:
>>> from tqdm.contrib.mytqdm import tqdm, trange
>>> for i in trange(10, api_key='{api_key}', title='{title}'):
...     ...

![link](https://mytqdm.app/)
"""
import logging
from os import getenv

try:
    import requests
except ImportError:
    raise ImportError("Please `pip install requests`")

from ..auto import tqdm as tqdm_auto

__author__ = {"github.com/padmalcom"}
__all__ = ['mytqdm', 'mytqdmrange', 'tqdm', 'trange']

class mytqdm(tqdm_auto):
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

    PROGRESS_URL = "https://mytqdm.app/api/v1/p"
    
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
            self.api_key = kwargs.pop('api_key', getenv("MYTQDM_API_KEY"))
            self.title = kwargs.pop('title', getenv("MYTQDM_TITLE"))
        super().__init__(*args, **kwargs)

    def display(self, msg=None, pos=None):
        super().display(msg=msg, pos=pos)
        current = self.n
        total = self.total
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
            resp = requests.post(self.PROGRESS_URL, json=payload, headers=headers, timeout=10)
            if resp.ok:
                logging.debug("mytqdm state successfully updated.")
            else:
                logging.warning(f"Got non-ok response from mytqdm {resp.status_code}")
        except requests.exceptions.Timeout:
            logging.error("The request to mytqdm.app timed out (connect or read).")
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occured when updating mytqdm state: {e}")

def mytqdmrange(*args, **kwargs):
    """Shortcut for `tqdm.contrib.mytqdm.tqdm(range(*args), **kwargs)`."""
    return mytqdm(range(*args), **kwargs)

# Aliases
tqdm = mytqdm
trange = mytqdmrange
