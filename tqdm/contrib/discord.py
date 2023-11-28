import logging
from os import getenv
import asyncio

try:
    import discord
except ImportError:
    raise ImportError("Please `pip install discord.py`")

from ..auto import tqdm as tqdm_auto
from .utils_worker import MonoWorker

__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['DiscordIO', 'tqdm_discord', 'tdrange', 'tqdm', 'trange']


class DiscordIO(MonoWorker):
    """Non-blocking file-like IO using a Discord Bot."""
    def __init__(self):
        super(DiscordIO, self).__init__()
        self.text = self.__class__.__name__
        self.message = None

    @classmethod
    def from_token(cls, token, channel_id):
        """Create a new DiscordIO instance using a bot token and channel ID."""
        instance = cls()
        instance.channel_id = channel_id
        instance.token = token
        try:
            intents = discord.Intents(messages=True, guilds=True)
            instance.client = discord.Client(intents=intents)
            instance.loop = asyncio.get_event_loop()
            instance.loop.create_task(instance.start_bot())
            # Wait for the bot to be ready before continuing
            instance.loop.run_until_complete(instance.client.wait_until_ready())
            # Attempt to get the channel
            channel = instance.client.get_channel(int(channel_id))
            if channel:
                # Ensure the bot has the necessary permissions to send messages
                if channel.permissions_for(channel.guild.me).send_messages:
                    # Send the initial message and store it in self.message
                    instance.message = instance.loop.run_until_complete(channel.send(instance.text))
                else:
                    tqdm_auto.write("Error: Bot doesn't have permission to send messages to the channel.")
            else:
                tqdm_auto.write(f"Error: Unable to find channel with ID {channel_id}")
        except Exception as e:
            tqdm_auto.write(str(e))
        return instance

    @classmethod
    def from_webhook(cls, webhook_url):
        """Create a new DiscordIO instance using a webhook URL."""
        instance = cls()
        instance.webhook_url = webhook_url
        try:
            webhook = discord.SyncWebhook.from_url(webhook_url)
            instance.message = webhook.send(instance.text, wait=True)
        except Exception as e:
            tqdm_auto.write(str(e))
        return instance

    async def start_bot(self):
        await self.client.start(self.token)

    def _edit_message(self, content):
        """Wraps the `message.edit` method to make the `content` keyword argument positional."""
        if hasattr(self, "loop"):
            self.loop.run_until_complete(self.message.edit(content=content))
        else:
            self.message.edit(content=content)

    def write(self, s):
        """Replaces internal `message`'s text with `s`."""
        if not s:
            s = "..."
        s = s.replace('\r', '').strip()
        if s == self.text or self.message is None:
            return  # skip duplicate message or if message is not available
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

    - create a discord bot (not public, no requirement of OAuth2 code
      grant, only send message permissions) & invite it to a channel:
      <https://discordpy.readthedocs.io/en/latest/discord.html>
    - copy the bot `{token}` & `{channel_id}` and paste below

    >>> from tqdm.contrib.discord import tqdm, trange
    >>> for i in tqdm(iterable, token='{token}', channel_id='{channel_id}'):
    ...     ...
    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        token  : str, required if not using webhook_url. Discord token
            [default: ${TQDM_DISCORD_TOKEN}].
        channel_id  : int, required if not using webhook_url. Discord channel ID
            [default: ${TQDM_DISCORD_CHANNEL_ID}].
        webhook_url  : str, required if not using token and channel_id. Discord channel webhook url
            [default: ${TQDM_DISCORD_WEBHOOK_URL}].
        webhook: bool, optional. If True, use a webhook instead of a bot. Defaults to False.
        mininterval  : float, optional.
          Minimum of [default: 1.5] to avoid rate limit.

        See `tqdm.auto.tqdm.__init__` for other parameters.
        """
        if not kwargs.get('disable'):
            kwargs = kwargs.copy()
            logging.getLogger("HTTPClient").setLevel(logging.WARNING)
            if kwargs.get("webhook", False):
                self.dio = DiscordIO.from_webhook(
                    webhook_url=kwargs.pop('webhook_url', getenv("TQDM_DISCORD_WEBHOOK_URL"))
                    )
            else:
                self.dio = DiscordIO.from_token(
                    token=kwargs.pop('token', getenv("TQDM_DISCORD_TOKEN")),
                    channel_id=kwargs.pop('channel_id', getenv("TQDM_DISCORD_CHANNEL_ID"))
                    )
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
    """Shortcut for `tqdm.contrib.discord.tqdm(range(*args), **kwargs)`."""
    return tqdm_discord(range(*args), **kwargs)


# Aliases
tqdm = tqdm_discord
trange = tdrange
