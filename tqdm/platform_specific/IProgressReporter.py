from abc import ABC, abstractmethod


class IProgressReporter(ABC):
    """An interface for outputting progress."""

    __slots__ = ()

    @abstractmethod
    def __init__(self, total: int = None, unit: str = ""):
        """Since costruction code is VERY specific and must be present, it is abstract"""
        raise NotImplementedError()

    @abstractmethod
    def progress(self, current: int, speed: float):
        """Sets current progress. `current` is the current progress, `speed` is its time derivative."""
        raise NotImplementedError()

    def message(self, msg: str):
        """Sets the message."""
        pass

    def prefix(self, prefix: str) -> None:
        """Sets the prefix."""
        pass

    def postfix(self, postfix: str) -> None:
        """Sets the postfix."""
        pass

    @abstractmethod
    def success(self) -> None:
        """Reports to the user that the task has finished without any errors."""
        raise NotImplementedError()

    @abstractmethod
    def fail(self, reason: str = None):
        """Reports the failure to the user."""
        raise NotImplementedError()

    @abstractmethod
    def clear(self):
        """Removes the reporter."""
        raise NotImplementedError()

    @abstractmethod
    def __enter__(self):
        raise NotImplementedError()

    @abstractmethod
    def __exit__(self, exception_type, exception_value, traceback):
        raise NotImplementedError()


class DummyProgressReporter(IProgressReporter):
    """Used instead of the progress reporter using unsupported features"""

    def __init__(self, total: int = None, unit: str = ""):
        pass

    def progress(self, current: int, speed: float):
        pass

    def fail(self, reason: str = None):
        pass

    def success(self):
        pass

    def clear(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass
