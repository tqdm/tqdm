# pylint: disable=missing-module-docstring, missing-class-docstring
# pylint: disable=missing-function-docstring, no-self-use
from __future__ import absolute_import

import logging
import logging.handlers
import sys
from io import StringIO

import pytest

from tqdm import tqdm
from tqdm.contrib.logging import _get_first_found_console_logging_handler
from tqdm.contrib.logging import _TqdmLoggingHandler as TqdmLoggingHandler
from tqdm.contrib.logging import logging_redirect_tqdm, tqdm_logging_redirect

from .tests_tqdm import importorskip

LOGGER = logging.getLogger(__name__)

TEST_LOGGING_FORMATTER = logging.Formatter()


class CustomTqdm(tqdm):
    messages = []

    @classmethod
    def write(cls, s, **__):  # pylint: disable=arguments-differ
        CustomTqdm.messages.append(s)


class ErrorRaisingTqdm(tqdm):
    exception_class = RuntimeError

    @classmethod
    def write(cls, s, **__):  # pylint: disable=arguments-differ
        raise ErrorRaisingTqdm.exception_class('fail fast')


class TestTqdmLoggingHandler:
    def test_should_call_tqdm_write(self):
        CustomTqdm.messages = []
        logger = logging.Logger('test')
        logger.handlers = [TqdmLoggingHandler(CustomTqdm)]
        logger.info('test')
        assert CustomTqdm.messages == ['test']

    def test_should_call_handle_error_if_exception_was_thrown(self):
        patch = importorskip('unittest.mock').patch
        logger = logging.Logger('test')
        ErrorRaisingTqdm.exception_class = RuntimeError
        handler = TqdmLoggingHandler(ErrorRaisingTqdm)
        logger.handlers = [handler]
        with patch.object(handler, 'handleError') as mock:
            logger.info('test')
            assert mock.called

    @pytest.mark.parametrize('exception_class', [
        KeyboardInterrupt,
        SystemExit
    ])
    def test_should_not_swallow_certain_exceptions(self, exception_class):
        logger = logging.Logger('test')
        ErrorRaisingTqdm.exception_class = exception_class
        handler = TqdmLoggingHandler(ErrorRaisingTqdm)
        logger.handlers = [handler]
        with pytest.raises(exception_class):
            logger.info('test')


class TestGetFirstFoundConsoleLoggingHandler:
    def test_should_return_none_for_no_handlers(self):
        assert _get_first_found_console_logging_handler([]) is None

    def test_should_return_none_without_stream_handler(self):
        handler = logging.handlers.MemoryHandler(capacity=1)
        assert _get_first_found_console_logging_handler([handler]) is None

    def test_should_return_none_for_stream_handler_not_stdout_or_stderr(self):
        handler = logging.StreamHandler(StringIO())
        assert _get_first_found_console_logging_handler([handler]) is None

    def test_should_return_stream_handler_if_stream_is_stdout(self):
        handler = logging.StreamHandler(sys.stdout)
        assert _get_first_found_console_logging_handler([handler]) == handler

    def test_should_return_stream_handler_if_stream_is_stderr(self):
        handler = logging.StreamHandler(sys.stderr)
        assert _get_first_found_console_logging_handler([handler]) == handler


class TestRedirectLoggingToTqdm:
    def test_should_add_and_remove_tqdm_handler(self):
        logger = logging.Logger('test')
        with logging_redirect_tqdm(loggers=[logger]):
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], TqdmLoggingHandler)
        assert not logger.handlers

    def test_should_remove_and_restore_console_handlers(self):
        logger = logging.Logger('test')
        stderr_console_handler = logging.StreamHandler(sys.stderr)
        stdout_console_handler = logging.StreamHandler(sys.stderr)
        logger.handlers = [stderr_console_handler, stdout_console_handler]
        with logging_redirect_tqdm(loggers=[logger]):
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], TqdmLoggingHandler)
        assert logger.handlers == [stderr_console_handler, stdout_console_handler]

    def test_should_inherit_console_logger_formatter(self):
        logger = logging.Logger('test')
        formatter = logging.Formatter('custom: %(message)s')
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.handlers = [console_handler]
        with logging_redirect_tqdm(loggers=[logger]):
            assert logger.handlers[0].formatter == formatter

    def test_should_not_remove_stream_handlers_not_for_stdout_or_stderr(self):
        logger = logging.Logger('test')
        stream_handler = logging.StreamHandler(StringIO())
        logger.addHandler(stream_handler)
        with logging_redirect_tqdm(loggers=[logger]):
            assert len(logger.handlers) == 2
            assert logger.handlers[0] == stream_handler
            assert isinstance(logger.handlers[1], TqdmLoggingHandler)
        assert logger.handlers == [stream_handler]


class TestTqdmWithLoggingRedirect:
    def test_should_add_and_remove_handler_from_root_logger_by_default(self):
        original_handlers = list(logging.root.handlers)
        with tqdm_logging_redirect(total=1) as pbar:
            assert isinstance(logging.root.handlers[-1], TqdmLoggingHandler)
            LOGGER.info('test')
            pbar.update(1)
        assert logging.root.handlers == original_handlers

    def test_should_add_and_remove_handler_from_custom_logger(self):
        logger = logging.Logger('test')
        with tqdm_logging_redirect(total=1, loggers=[logger]) as pbar:
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], TqdmLoggingHandler)
            logger.info('test')
            pbar.update(1)
        assert not logger.handlers

    def test_should_not_fail_with_logger_without_console_handler(self):
        logger = logging.Logger('test')
        logger.handlers = []
        with tqdm_logging_redirect(total=1, loggers=[logger]):
            logger.info('test')
        assert not logger.handlers

    def test_should_format_message(self):
        logger = logging.Logger('test')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            r'prefix:%(message)s'
        ))
        logger.handlers = [console_handler]
        CustomTqdm.messages = []
        with tqdm_logging_redirect(loggers=[logger], tqdm_class=CustomTqdm):
            logger.info('test')
        assert CustomTqdm.messages == ['prefix:test']

    def test_use_root_logger_by_default_and_write_to_custom_tqdm(self):
        logger = logging.root
        CustomTqdm.messages = []
        with tqdm_logging_redirect(total=1, tqdm_class=CustomTqdm) as pbar:
            assert isinstance(pbar, CustomTqdm)
            logger.info('test')
            assert CustomTqdm.messages == ['test']
