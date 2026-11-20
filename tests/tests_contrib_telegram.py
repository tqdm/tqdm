from io import StringIO
from unittest.mock import patch

import pytest

pytest.importorskip("requests")
from tqdm.contrib import telegram  # noqa: E402


@pytest.mark.parametrize("options", [
    {"disable": True}, {"disable": None}, {"delay": 60}, {"delay": 60, "leave": False},
])
def test_no_telegram_message_without_a_visible_bar(options):
    with patch.object(telegram, "TelegramIO") as sender:
        with telegram.tqdm(total=1, file=StringIO(), **options) as bar:
            bar.update()
        sender.assert_not_called()


def test_visible_telegram_bar_uses_one_message():
    with patch.object(telegram, "TelegramIO") as sender:
        with telegram.tqdm(total=2, token="example", chat_id="chat", file=StringIO(),
                           leave=False, mininterval=0) as bar:
            bar.update()
            bar.update()
        sender.assert_called_once_with("example", "chat")
        assert sender.return_value.write.called
        sender.return_value.delete.assert_called_once_with()


def test_delayed_telegram_bar_can_display_later():
    with patch.object(telegram, "TelegramIO") as sender:
        with telegram.tqdm(total=2, delay=60, mininterval=0, file=StringIO()) as bar:
            bar.clear()
            sender.assert_not_called()
            bar.start_t -= 61
            bar.update()
            sender.assert_called_once()
