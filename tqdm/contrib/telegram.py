"""
Sends updates to a Telegram bot.
"""
from __future__ import absolute_import

from concurrent.futures import ThreadPoolExecutor
from requests import Session

from tqdm.auto import tqdm as tqdm_auto
from tqdm.utils import _range
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['TelegramIO', 'tqdm_telegram', 'ttgrange', 'tqdm', 'trange']


class TelegramIO():
    """Non-blocking file-like IO to a Telegram Bot."""
    API = 'https://api.telegram.org/bot'

    def __init__(self, token, chat_id):
        """Creates a new message in the given `chat_id`."""
        self.token = token
        self.chat_id = chat_id
        self.session = session = Session()
        self.text = self.__class__.__name__
        self.pool = ThreadPoolExecutor()
        self.futures = []
        try:
            res = session.post(
                self.API + '%s/sendMessage' % self.token,
                data=dict(text='`' + self.text + '`', chat_id=self.chat_id,
                          parse_mode='MarkdownV2'))
        except Exception as e:
            tqdm_auto.write(str(e))
        else:
            self.message_id = res.json()['result']['message_id']

    def write(self, s):
        """Replaces internal `message_id`'s text with `s`."""
        if not s:
            return
        s = s.strip().replace('\r', '')
        if s == self.text:
            return  # avoid duplicate message Bot error
        self.text = s
        try:
            f = self.pool.submit(
                self.session.post,
                self.API + '%s/editMessageText' % self.token,
                data=dict(
                    text='`' + s + '`', chat_id=self.chat_id,
                    message_id=self.message_id, parse_mode='MarkdownV2'))
        except Exception as e:
            tqdm_auto.write(str(e))
        else:
            self.futures.append(f)
            return f

    def flush(self):
        """Ensure the last `write` has been processed."""
        [f.cancel() for f in self.futures[-2::-1]]
        try:
            return self.futures[-1].result()
        except IndexError:
            pass
        finally:
            self.futures = []

    def __del__(self):
        self.flush()


class tqdm_telegram(tqdm_auto):
    """
    Standard `tqdm.auto.tqdm` but also sends updates to a Telegram bot.
    May take a few seconds to create (`__init__`) and clear (`__del__`).

    >>> from tqdm.contrib.telegram import tqdm, trange
    >>> for i in tqdm(
    ...     iterable,
    ...     token='1234567890:THIS1SSOMETOKEN0BTAINeDfrOmTELEGrAM',
    ...     chat_id='0246813579'):
    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        token  : str, required. Telegram token.
        chat_id  : str, required. Telegram chat ID.

        See `tqdm.auto.tqdm.__init__` for other parameters.
        """
        self.tgio = TelegramIO(kwargs.pop('token'), kwargs.pop('chat_id'))
        super(tqdm_telegram, self).__init__(*args, **kwargs)

    def display(self, **kwargs):
        super(tqdm_telegram, self).display(**kwargs)
        fmt = self.format_dict
        if 'bar_format' in fmt and fmt['bar_format']:
            fmt['bar_format'] = fmt['bar_format'].replace('<bar/>', '{bar}')
        else:
            fmt['bar_format'] = '{l_bar}{bar}{r_bar}'
        fmt['bar_format'] = fmt['bar_format'].replace('{bar}', '{bar:10u}')
        self.tgio.write(self.format_meter(**fmt))

    def __new__(cls, *args, **kwargs):
        """
        Workaround for mixed-class same-stream nested progressbars.
        See [#509](https://github.com/tqdm/tqdm/issues/509)
        """
        with cls.get_lock():
            try:
                cls._instances = tqdm_auto._instances
            except AttributeError:
                pass
        instance = super(tqdm_telegram, cls).__new__(cls, *args, **kwargs)
        with cls.get_lock():
            try:
                # `tqdm_auto` may have been changed so update
                cls._instances.update(tqdm_auto._instances)
            except AttributeError:
                pass
            tqdm_auto._instances = cls._instances
        return instance


def ttgrange(*args, **kwargs):
    """
    A shortcut for `tqdm.contrib.telegram.tqdm(xrange(*args), **kwargs)`.
    On Python3+, `range` is used instead of `xrange`.
    """
    return tqdm_telegram(_range(*args), **kwargs)


# Aliases
tqdm = tqdm_telegram
trange = ttgrange
