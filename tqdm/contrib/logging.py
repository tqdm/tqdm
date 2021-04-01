
"""
Enables multiple commonly used features relating to logging
in combination with tqdm.
"""
from __future__ import absolute_import

import logging
import sys
from contextlib import contextmanager

try:
    from typing import Iterator, List, Optional, Type  # pylint: disable=unused-import
except ImportError:
    # we may ignore type hints
    pass

from ..std import tqdm as _tqdm


class _TqdmLoggingHandler(logging.StreamHandler):
    def __init__(
        self,
        tqdm=None  # type: Optional[Type[tqdm.tqdm]]
    ):
        super(  # pylint: disable=super-with-arguments
            _TqdmLoggingHandler, self
        ).__init__()
        if tqdm is None:
            tqdm = _tqdm
        self.tqdm = tqdm

    def emit(self, record):
        try:
            msg = self.format(record)
            self.tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # noqa pylint: disable=bare-except
            self.handleError(record)


def _is_console_logging_handler(handler):
    return (
        isinstance(handler, logging.StreamHandler)
        and handler.stream in {sys.stdout, sys.stderr}
    )


def _get_first_found_console_logging_formatter(handlers):
    for handler in handlers:
        if _is_console_logging_handler(handler):
            return handler.formatter
    return None


@contextmanager
def redirect_logging_to_tqdm(
    loggers=None,  # type: Optional[List[logging.Logger]],
    tqdm=None  # type: Optional[Type[tqdm.tqdm]]
):
    # type: (...) -> Iterator[None]
    """
    Context manager for redirecting logging console output to tqdm.
    Logging to other logging handlers, such as a log file,
    will not be affected.

    By default the, the handlers of the root logger will be amended.
    (for the duration of the context)
    You may also provide a list of `loggers` instead
    (e.g. if a particular logger doesn't fallback to the root logger)

    Example:

    ```python
    import logging
    from tqdm.contrib.logging import redirect_logging_to_tqdm

    LOGGER = logging.getLogger(__name__)

    if __name__ == '__main__':
        logging.basicConfig(level='INFO')
        with redirect_logging_to_tqdm():
            # logging to the console is now redirected to tqdm
            LOGGER.info('some message')
        # logging is now restored
    ```
    """
    if loggers is None:
        loggers = [logging.root]
    original_handlers_list = [
        logger.handlers for logger in loggers
    ]
    try:
        for logger in loggers:
            tqdm_handler = _TqdmLoggingHandler(tqdm)
            tqdm_handler.setFormatter(
                _get_first_found_console_logging_formatter(
                    logger.handlers
                )
            )
            logger.handlers = [
                handler
                for handler in logger.handlers
                if not _is_console_logging_handler(handler)
            ] + [tqdm_handler]
        yield
    finally:
        for logger, original_handlers in zip(loggers, original_handlers_list):
            logger.handlers = original_handlers


def _pop_optional(
    kwargs,  # type: dict
    key,  # type: str
    default_value=None
):
    try:
        return kwargs.pop(key)
    except KeyError:
        return default_value


@contextmanager
def tqdm_with_logging_redirect(
    *args,
    # loggers=None,  # type: Optional[List[logging.Logger]]
    # tqdm=None,  # type: Optional[Type[tqdm.tqdm]]
    **kwargs
):
    # type: (...) -> Iterator[None]
    """
    Similar to `redirect_logging_to_tqdm`,
    but provides a context manager wrapping tqdm.

    All parameters, except `loggers` and `tqdm`, will get passed on to `tqdm`.

    By default this will wrap `tqdm.tqdm`.
    You may pass your own `tqdm` class if desired.

    Example:

    ```python
    import logging
    from tqdm.contrib.logging import tqdm_with_logging_redirect

    LOGGER = logging.getLogger(__name__)

    if __name__ == '__main__':
        logging.basicConfig(level='INFO')

        file_list = ['file1', 'file2']
        with tqdm_with_logging_redirect(total=len(file_list)) as pbar:
            # logging to the console is now redirected to tqdm
            for filename in file_list:
                LOGGER.info('processing file: %s', filename)
                pbar.update(1)
        # logging is now restored
    ```

    A more advanced example with non-default tqdm class and loggers:

    ```python
    import logging
    from tqdm.auto import tqdm
    from tqdm.contrib.logging import tqdm_with_logging_redirect

    LOGGER = logging.getLogger(__name__)

    if __name__ == '__main__':
        logging.basicConfig(level='INFO')

        file_list = ['file1', 'file2']
        with tqdm_with_logging_redirect(
            total=len(file_list),
            tqdm=tqdm,
            loggers=[LOGGER]
        ) as pbar:
            # logging to the console is now redirected to tqdm
            for filename in file_list:
                LOGGER.info('processing file: %s', filename)
                pbar.update(1)
        # logging is now restored
    ```

    """
    loggers = _pop_optional(kwargs, 'loggers')
    tqdm = _pop_optional(kwargs, 'tqdm')
    if tqdm is None:
        tqdm = _tqdm
    with tqdm(*args, **kwargs) as pbar:
        with redirect_logging_to_tqdm(loggers=loggers, tqdm=tqdm):
            yield pbar
