"""
Sends updates to a Discord bot.
"""
from __future__ import absolute_import

from concurrent.futures import ThreadPoolExecutor
try:
    from disco.client import Client, ClientConfig
except ImportError:
    raise ImportError("Please `pip install disco-py`")

from tqdm.auto import tqdm as tqdm_auto
from tqdm.utils import _range
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['DiscordIO', 'tqdm_discord', 'tdrange', 'tqdm', 'trange']


class DiscordIO():
    """Non-blocking file-like IO to using a Discord Bot."""
    def __init__(self, token, channel_id):
        """Creates a new message in the given `channel_id`."""
        config = ClientConfig()
        config.token = token
        client = Client(config)
        self.text = self.__class__.__name__
        self.pool = ThreadPoolExecutor()
        self.futures = []
        try:
            self.msg = client.api.channels_messages_create(
                channel_id, self.text)
        except Exception as e:
            tqdm_auto.write(str(e))

    def write(self, s):
        """Replaces internal `message_id`'s text with `s`."""
        if not s:
            return
        s = s.strip().replace('\r', '')
        if s == self.text:
            return  # avoid duplicate message Bot error
        self.text = s
        try:
            f = self.pool.submit(self.msg.edit, '`' + s + '`')
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


class tqdm_discord(tqdm_auto):
    """
    Standard `tqdm.auto.tqdm` but also sends updates to a Discord bot.
    May take a few seconds to create (`__init__`) and clear (`__del__`).

    >>> from tqdm.contrib.discord import tqdm, trange
    >>> for i in tqdm(
    ...     iterable,
    ...     token='THIS1SSOMETOKEN0BTAINeDfrOmD1SC0rd',
    ...     channel_id=0246813579):
    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        token  : str, required. Telegram token.
        chat_id  : str, required. Telegram chat ID.
        mininterval  : float, optional.
          Minimum of [default: 1.5] to avoid rate limit.

        See `tqdm.auto.tqdm.__init__` for other parameters.
        """
        self.dio = DiscordIO(kwargs.pop('token'), kwargs.pop('channel_id'))
        kwargs['mininterval'] = max(1.5, kwargs.get('mininterval', 1.5))
        super(tqdm_discord, self).__init__(*args, **kwargs)

    def display(self, **kwargs):
        super(tqdm_discord, self).display(**kwargs)
        fmt = self.format_dict
        if 'bar_format' in fmt and fmt['bar_format']:
            fmt['bar_format'] = fmt['bar_format'].replace('<bar/>', '{bar}')
        else:
            fmt['bar_format'] = '{l_bar}{bar}{r_bar}'
        fmt['bar_format'] = fmt['bar_format'].replace('{bar}', '{bar:10u}')
        self.dio.write(self.format_meter(**fmt))

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
        instance = super(tqdm_discord, cls).__new__(cls, *args, **kwargs)
        with cls.get_lock():
            try:
                # `tqdm_auto` may have been changed so update
                cls._instances.update(tqdm_auto._instances)
            except AttributeError:
                pass
            tqdm_auto._instances = cls._instances
        return instance


def tdrange(*args, **kwargs):
    """
    A shortcut for `tqdm.contrib.discord.tqdm(xrange(*args), **kwargs)`.
    On Python3+, `range` is used instead of `xrange`.
    """
    return tqdm_discord(_range(*args), **kwargs)


# Aliases
tqdm = tqdm_discord
trange = tdrange
