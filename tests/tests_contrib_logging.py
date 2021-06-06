# pylint: disable=missing-module-docstring, missing-class-docstring
# pylint: disable=missing-function-docstring, no-self-use
from __future__ import absolute_import

import logging
import logging.handlers
import sys
from contextlib import contextmanager
from io import StringIO

try:
    from typing import Iterator, List, Optional  # pylint: disable=unused-import
except ImportError:
    pass

import pytest

from tqdm import tqdm
from tqdm.contrib.logging import LOGGER as DEFAULT_LOGGER
from tqdm.contrib.logging import _get_first_found_console_logging_formatter
from tqdm.contrib.logging import _TqdmLoggingHandler as TqdmLoggingHandler
from tqdm.contrib.logging import (
    logging_redirect_tqdm, logging_tqdm, tqdm_logging_redirect)

from .tests_tqdm import importorskip

LOGGER = logging.getLogger(__name__)

TEST_LOGGING_FORMATTER = logging.Formatter()


class CustomTqdm(tqdm):
    messages = []  # type: List[str]

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


class TestGetFirstFoundConsoleLoggingFormatter:
    def test_should_return_none_for_no_handlers(self):
        assert _get_first_found_console_logging_formatter([]) is None

    def test_should_return_none_without_stream_handler(self):
        handler = logging.handlers.MemoryHandler(capacity=1)
        handler.formatter = TEST_LOGGING_FORMATTER
        assert _get_first_found_console_logging_formatter([handler]) is None

    def test_should_return_none_for_stream_handler_not_stdout_or_stderr(self):
        handler = logging.StreamHandler(StringIO())
        handler.formatter = TEST_LOGGING_FORMATTER
        assert _get_first_found_console_logging_formatter([handler]) is None

    def test_should_return_stream_handler_formatter_if_stream_is_stdout(self):
        handler = logging.StreamHandler(sys.stdout)
        handler.formatter = TEST_LOGGING_FORMATTER
        assert _get_first_found_console_logging_formatter(
            [handler]
        ) == TEST_LOGGING_FORMATTER

    def test_should_return_stream_handler_formatter_if_stream_is_stderr(self):
        handler = logging.StreamHandler(sys.stderr)
        handler.formatter = TEST_LOGGING_FORMATTER
        assert _get_first_found_console_logging_formatter(
            [handler]
        ) == TEST_LOGGING_FORMATTER


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


@contextmanager
def add_capturing_logging_handler(
    logger  # type: logging.Logger
):
    # type: (...) -> Iterator[StringIO]
    try:
        previous_handlers = logger.handlers
        out = StringIO()
        stream_handler = logging.StreamHandler(out)
        logger.addHandler(stream_handler)
        yield out
    finally:
        logger.handlers = previous_handlers


class TestLoggingTqdm:
    @pytest.mark.parametrize(
        "logger_param,expected_logger",
        [
            (None, DEFAULT_LOGGER),
            (LOGGER, LOGGER)
        ]
    )
    def test_should_log_tqdm_output(
        self,
        logger_param,  # type: Optional[logging.Logger]
        expected_logger  # type: logging.Logger
    ):
        with add_capturing_logging_handler(expected_logger) as out:
            with logging_tqdm(total=2, logger=logger_param, mininterval=0) as pbar:
                pbar.update(1)
            last_log_line = out.getvalue().splitlines()[-1]
        assert '50%' in last_log_line
        assert '1/2' in last_log_line

    def test_should_log_tqdm_output_using_iterable(self):
        with add_capturing_logging_handler(DEFAULT_LOGGER) as out:
            processed_items = list(logging_tqdm(range(2), mininterval=0))
            assert processed_items == [0, 1]
            out_lines = out.getvalue().splitlines()
        assert len(out_lines) == 2
        assert '1/2' in out_lines[0]
        assert '2/2' in out_lines[1]

    def test_should_not_output_before_any_progress(self):
        with add_capturing_logging_handler(DEFAULT_LOGGER) as out:
            with logging_tqdm(total=2, mininterval=0) as _:
                pass
            assert out.getvalue() == ''

    def test_should_use_default_message_if_msg_is_none(self):
        with add_capturing_logging_handler(DEFAULT_LOGGER) as out:
            with logging_tqdm(total=2, mininterval=0) as pbar:
                pbar.n = 1
                pbar.display()
                out_lines = out.getvalue().splitlines()
            assert len(out_lines) == 1
            assert '1/2' in out_lines[-1]

    def test_should_not_output_if_msg_is_empty(self):
        with add_capturing_logging_handler(DEFAULT_LOGGER) as out:
            with logging_tqdm(total=2, mininterval=0) as pbar:
                pbar.n = 1
                pbar.display(msg='')
            assert out.getvalue() == ''

    def test_should_not_log_same_n_twice(self):
        with add_capturing_logging_handler(DEFAULT_LOGGER) as out:
            with logging_tqdm(total=2, mininterval=0) as pbar:
                # update with call display
                pbar.update(1)
                # another call to display would cause the same message
                pbar.display()
                out_lines = out.getvalue().splitlines()
            assert len(out_lines) == 1
            assert '1/2' in out_lines[-1]

    def test_should_only_allow_iterable_as_positional_arg(self):
        # with add_capturing_logging_handler(DEFAULT_LOGGER) as out:
        with pytest.raises(ValueError):
            list(logging_tqdm(range(2), 'other'))
        #     assert processed_items == [0, 1]
        #     out_lines = out.getvalue().splitlines()
        # assert len(out_lines) == 2
        # assert '1/2' in out_lines[0]
        # assert '2/2' in out_lines[1]
