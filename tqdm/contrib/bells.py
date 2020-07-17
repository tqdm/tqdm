"""
Even more features than `tqdm.auto` (all the bells & whistles):

- `tqdm.auto`
- `tqdm.tqdm.pandas`
- `tqdm.contrib.telegram`
    + uses `${TQDM_TELEGRAM_TOKEN}` and `${TQDM_TELEGRAM_CHAT_ID}`
- `tqdm.contrib.discord`
    + uses `${TQDM_DISCORD_TOKEN}` and `${TQDM_DISCORD_CHANNEL_ID}`
"""
__all__ = ['tqdm', 'trange']
from os import getenv
import warnings


if getenv("TQDM_TELEGRAM_TOKEN") and getenv("TQDM_TELEGRAM_CHAT_ID"):
    from tqdm.contrib.telegram import tqdm, trange
elif getenv("TQDM_DISCORD_TOKEN") and getenv("TQDM_DISCORD_CHANNEL_ID"):
    from tqdm.contrib.discord import tqdm, trange
else:
    from tqdm.auto import tqdm, trange

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    tqdm.pandas()
