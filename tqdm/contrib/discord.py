"""
Sends updates to a Discord bot.

Usage:
>>> from tqdm.contrib.discord import tqdm, trange
>>> for i in trange(10, webhook_url='{webhook_url}'):
...     ...

![screenshot](https://img.tqdm.ml/screenshot-discord.png)
"""
from __future__ import absolute_import

import logging
from os import getenv

try:
    import discord
except ImportError:
    raise ImportError("Please `pip install discord.py requests`")

from ..auto import tqdm as tqdm_auto
from ..utils import _range
from .utils_worker import MonoWorker

__author__ = {"github.com/": ["casperdcl", "xx-05"]}
__all__ = ['DiscordIO', 'tqdm_discord', 'tdrange', 'tqdm', 'trange']


class DiscordIO(MonoWorker):
    """Non-blocking file-like IO using a Discord Bot."""
    def __init__(self, webhook_url):
        """Creates a new message on a channel via the given `webhook_url`."""
        super(DiscordIO, self).__init__()

        webhook = discord.SyncWebhook.from_url(webhook_url)
        self.text = self.__class__.__name__

        try:
            self.message = webhook.send(self.text, wait=True)
        except Exception as e:
            tqdm_auto.write(str(e))
            self.message = None

    def _edit_message(self, content):
        """Wraps the `message.edit` method to make the `content` keyword argument positional."""
        self.message.edit(content=content)

    def write(self, s):
        """Replaces internal `message`'s text with `s`."""
        if not s:
            s = "..."
        s = s.replace('\r', '').strip()
        if s == self.text:
            return  # skip duplicate message
        message = self.message
        if message is None:
            return
        self.text = s
        try:
            future = self.submit(self._edit_message, '`' + s + '`')
        except Exception as e:
            tqdm_auto.write(str(e))
        else:
            return future


class tqdm_discord(tqdm_auto):
    """
    Standard `tqdm.auto.tqdm` but also sends updates to a Discord Bot.
    May take a few seconds to create (`__init__`).

    - add a webhook to a server channel:
        (Edit Channel -> Integrations -> Webhooks -> New Webhook)
    - copy the `{webhook_url}` into the tqdm_discord constructor

    >>> from tqdm.contrib.discord import tqdm, trange
    >>> for i in tqdm(iterable, webhook_url='{webhook_url}'):
    ...     ...
    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        webhook_url  : str, required. Discord channel webhook url
            [default: ${TQDM_DISCORD_WEBHOOK_URL}].
        mininterval  : float, optional.
          Minimum of [default: 1.5] to avoid rate limit.

        See `tqdm.auto.tqdm.__init__` for other parameters.
        """
        if not kwargs.get('disable'):
            kwargs = kwargs.copy()
            logging.getLogger("HTTPClient").setLevel(logging.WARNING)
            self.dio = DiscordIO(
                webhook_url=kwargs.pop('webhook_url', getenv("TQDM_DISCORD_WEBHOOK_URL")))
            kwargs['mininterval'] = max(1.5, kwargs.get('mininterval', 1.5))
        super(tqdm_discord, self).__init__(*args, **kwargs)

    def display(self, **kwargs):
        super(tqdm_discord, self).display(**kwargs)
        fmt = self.format_dict
        if fmt.get('bar_format', None):
            fmt['bar_format'] = fmt['bar_format'].replace(
                '<bar/>', '{bar:10u}').replace('{bar}', '{bar:10u}')
        else:
            fmt['bar_format'] = '{l_bar}{bar:10u}{r_bar}'
        self.dio.write(self.format_meter(**fmt))

    def clear(self, *args, **kwargs):
        super(tqdm_discord, self).clear(*args, **kwargs)
        if not self.disable:
            self.dio.write("")


def tdrange(*args, **kwargs):
    """
    A shortcut for `tqdm.contrib.discord.tqdm(xrange(*args), **kwargs)`.
    On Python3+, `range` is used instead of `xrange`.

    Parameters:
    ----------
    webhook_url  : str, required. Discord webhook url
        [default: ${TQDM_DISCORD_WEBHOOK_URL}].
    """
    return tqdm_discord(_range(*args), **kwargs)


# Aliases
tqdm = tqdm_discord
trange = tdrange
