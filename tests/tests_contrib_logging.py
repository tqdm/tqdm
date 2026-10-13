import logging
import logging.handlers
import sys
from io import StringIO

from pytest import fixture, mark, raises

from tqdm import tqdm
from tqdm.contrib.logging import _get_first_found_console_logging_handler
from tqdm.contrib.logging import _TqdmLoggingHandler as TqdmLoggingHandler
from tqdm.contrib.logging import logging_redirect_tqdm, tqdm_logging_redirect

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


@fixture
def logger():
    """Standalone (unregistered) logger"""
    return logging.Logger('test')


@fixture
def messages():
    """Freshly emptied `CustomTqdm.messages`"""
    CustomTqdm.messages = []
    return CustomTqdm.messages


class TestTqdmLoggingHandler:
    def test_should_call_tqdm_write(self, logger, messages):
        logger.handlers = [TqdmLoggingHandler(CustomTqdm)]
        logger.info('test')
        assert messages == ['test']

    def test_should_call_handle_error_if_exception_was_thrown(self, logger, monkeypatch):
        ErrorRaisingTqdm.exception_class = RuntimeError
        handler = TqdmLoggingHandler(ErrorRaisingTqdm)
        logger.handlers = [handler]
        errors = []
        monkeypatch.setattr(handler, 'handleError', errors.append)
        logger.info('test')
        assert errors

    @mark.parametrize('exception_class', [KeyboardInterrupt, SystemExit])
    def test_should_not_swallow_certain_exceptions(self, logger, exception_class):
        ErrorRaisingTqdm.exception_class = exception_class
        logger.handlers = [TqdmLoggingHandler(ErrorRaisingTqdm)]
        with raises(exception_class):
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
    def test_should_add_and_remove_tqdm_handler(self, logger):
        with logging_redirect_tqdm(loggers=[logger]):
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], TqdmLoggingHandler)
        assert not logger.handlers

    def test_should_remove_and_restore_console_handlers(self, logger):
        stderr_console_handler = logging.StreamHandler(sys.stderr)
        stdout_console_handler = logging.StreamHandler(sys.stderr)
        logger.handlers = [stderr_console_handler, stdout_console_handler]
        with logging_redirect_tqdm(loggers=[logger]):
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], TqdmLoggingHandler)
        assert logger.handlers == [stderr_console_handler, stdout_console_handler]

    def test_should_inherit_console_logger_formatter(self, logger):
        formatter = logging.Formatter('custom: %(message)s')
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.handlers = [console_handler]
        with logging_redirect_tqdm(loggers=[logger]):
            assert logger.handlers[0].formatter == formatter

    def test_should_inherit_console_handler_filters(self, logger, messages):
        class SuffixFilter(logging.Filter):
            def filter(self, record):
                record.msg = f'{record.msg} -- filter'
                return True

        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.addFilter(SuffixFilter())
        logger.handlers = [console_handler]
        with logging_redirect_tqdm(loggers=[logger], tqdm_class=CustomTqdm):
            logger.info('test')
        assert messages == ['test -- filter']

    def test_should_not_remove_stream_handlers_not_for_stdout_or_stderr(self, logger):
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

    def test_should_add_and_remove_handler_from_custom_logger(self, logger):
        with tqdm_logging_redirect(total=1, loggers=[logger]) as pbar:
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], TqdmLoggingHandler)
            logger.info('test')
            pbar.update(1)
        assert not logger.handlers

    def test_should_not_fail_with_logger_without_console_handler(self, logger):
        logger.handlers = []
        with tqdm_logging_redirect(total=1, loggers=[logger]):
            logger.info('test')
        assert not logger.handlers

    def test_should_format_message(self, logger, messages):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(r'prefix:%(message)s'))
        logger.handlers = [console_handler]
        with tqdm_logging_redirect(loggers=[logger], tqdm_class=CustomTqdm):
            logger.info('test')
        assert messages == ['prefix:test']

    def test_use_root_logger_by_default_and_write_to_custom_tqdm(self, messages):
        with tqdm_logging_redirect(total=1, tqdm_class=CustomTqdm) as pbar:
            assert isinstance(pbar, CustomTqdm)
            logging.root.info('test')
            assert messages == ['test']
