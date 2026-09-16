from unittest.mock import Mock

from pytest import importorskip, mark

importorskip("requests")

from tqdm.contrib import telegram  # noqa: E402


def test_delete_message(monkeypatch):
    session = Mock()
    session.post.return_value.json.return_value = {'result': {'message_id': 42}}
    monkeypatch.setattr(telegram, 'Session', lambda: session)
    stream = telegram.TelegramIO('test-token', 'test-chat')
    try:
        future = stream.delete()
        assert future.result(timeout=5) is session.post.return_value
        session.post.assert_called_with(
            'https://api.telegram.org/bottest-token/deleteMessage',
            data={'chat_id': 'test-chat', 'message_id': 42})
    finally:
        stream.pool.shutdown(wait=True)


@mark.parametrize('leave', [False, True])
def test_close_delete_message(monkeypatch, tmp_file, leave):
    session = Mock()
    session.post.return_value.json.return_value = {'result': {'message_id': 42}}
    monkeypatch.setattr(telegram, 'Session', lambda: session)
    bar = telegram.tqdm(total=1, token='test-token', chat_id='test-chat',
                        leave=leave, file=tmp_file)
    try:
        bar.update()
        bar.close()
    finally:
        bar.close()
        bar.tgio.pool.shutdown(wait=True)
    delete_calls = [call for call in session.post.call_args_list
                    if call.args[0].endswith('/deleteMessage')]
    assert len(delete_calls) == (0 if leave else 1)
    if not leave:
        assert delete_calls[0].args == ('https://api.telegram.org/bottest-token/deleteMessage',)
        assert delete_calls[0].kwargs == {'data': {'chat_id': 'test-chat', 'message_id': 42}}
