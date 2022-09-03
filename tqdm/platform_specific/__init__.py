__all__ = ("MetaReporter",)
import sys
import importlib

from .IProgressReporter import IProgressReporter

systemToReporterMapping = {
    "win32": ("windows_taskbar_extensions",),
    "linux": ("DBusTray", "UnityDBusTaskbarButton"),
}

reporterClassesToUse = []
if sys.platform in systemToReporterMapping:
    for modName in systemToReporterMapping[sys.platform]:
        mod = importlib.import_module("." + modName, __package__)
        cls = getattr(mod, mod.__all__[0])
        reporterClassesToUse.append(cls)


class MetaReporter(IProgressReporter):
    __slots__ = ("reporters", "reportersCandidates")

    def __init__(self, total: int = None, unit: str = "") -> None:
        self.reportersCandidates = []
        self.reporters = []
        for cls in reporterClassesToUse:
            self.reportersCandidates.append(cls(total, unit))

    def progress(self, current: int, speed: float) -> None:
        for rep in self.reporters:
            rep.progress(current, speed)

    def fail(self, reason: str = None):
        for rep in self.reporters:
            rep.fail(reason)

    def success(self) -> None:
        for rep in self.reporters:
            rep.success()

    def prefix(self, prefix: str) -> None:
        for rep in self.reporters:
            rep.prefix(prefix)

    def message(self, msg: str):
        for rep in self.reporters:
            rep.message(message)

    def postfix(self, postfix: str) -> None:
        for rep in self.reporters:
            rep.postfix(postfix)

    def __enter__(self) -> "MetaReporter":
        for rep in self.reportersCandidates:
            try:
                self.reporters.append(rep.__enter__())
            except BaseException:
                pass
        return self

    def __exit__(
        self, exception_type: None, exception_value: None, traceback: None
    ) -> None:
        for rep in self.reporters:
            rep.__exit__(exception_type, exception_value, traceback)

    def clear(self):
        for rep in self.reporters:
            rep.clear()
