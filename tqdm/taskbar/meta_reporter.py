import sys
import importlib
from functools import wraps
from .PlatformSpecificProgressReporter import PlatformSpecificProgressReporter
__all__ = ["MetaReporter"]

systemToReporterMapping={
    "win32": ("windows_taskbar_extensions", ),
    "linux": ("DBusTray", "UnityDBusTaskbarButton")
}

reporterClassesToUse=[]
if sys.platform in systemToReporterMapping:
    for modName in systemToReporterMapping[sys.platform]:
        mod=importlib.import_module("."+modName, __package__)
        cls=getattr(mod, mod.__all__[0])
        reporterClassesToUse.append(cls)

class MetaReporter(PlatformSpecificProgressReporter):
    __slots__=("reporters", "reportersCandidates")

    @wraps(PlatformSpecificProgressReporter.__init__)
    def __init__(self, *args, **kwargs):
        self.reportersCandidates=[]
        self.reporters=[]
        for cls in reporterClassesToUse:
            self.reportersCandidates.append(cls(*args, **kwargs))

    @wraps(PlatformSpecificProgressReporter.progress)
    def progress(self, *args, **kwargs):
        for rep in self.reporters:
            rep.progress(*args, **kwargs)

    def fail(self, reason:str=None):
        for rep in self.reporters:
            rep.fail(reason)

    def success(self):
        for rep in self.reporters:
            rep.success()

    def prefix(self, prefix:str):
        for rep in self.reporters:
            rep.prefix(prefix)

    def message(self, message:str):
        for rep in self.reporters:
            rep.message(message)

    def postfix(self, postfix:str):
        for rep in self.reporters:
            rep.postfix(postfix)

    def __enter__(self):
        for rep in self.reportersCandidates:
            #try:
            self.reporters.append(rep.__enter__())
            #except:
            #    pass
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for rep in self.reporters:
            rep.__exit__(exception_type, exception_value, traceback)

    def clear(self):
        for rep in self.reporters:
            rep.clear()
