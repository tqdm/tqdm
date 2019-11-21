__all__ = ("DBusProgressReporter",)

try:
    import sys
    from .PlatformSpecificProgressReporter import PlatformSpecificProgressReporter
    from dbus import SessionBus

    class DBusProgressReporter(PlatformSpecificProgressReporter):
        methodsNames = ("terminate", "setError", "setPercent", "setSpeed", "setTotalAmount", "setProcessedAmount", "setDescriptionField", "setInfoMessage")
        __slots__ = ("view", "viewPath", "unit", *methodsNames)
        bus = SessionBus()
        server = bus.get_object("org.kde.kuiserver", "/JobViewServer")
        interfaceName = "org.kde.JobViewV2"

        def __init__(self, total: int = None, unit: str = ""):
            self.viewPath = None
            self.view = None
            self.unit = unit
            self.total = total
            for mn in self.__class__.methodsNames:
                setattr(self, mn, None)

        def progress(self, current: int, speed: float = None):
            self.setProcessedAmount(current, self.unit)
            self.setPercent(current / self.total * 100)
            if speed is not None:
                self.setSpeed(speed)

        def fail(self, reason:str="Failed"):
            if self.view:
                self.setError(100)
                self.terminate(reason)
                self.__exit__(None, None, None)

        def success(self):
            self.terminate("")
            self.__exit__(None, None, None)
        
        def prefix(self, prefix:str):
            if isinstance(prefix, str):
                self.setDescriptionField(0, "Description:", prefix)

        def postfix(self, postfix:str):
            if isinstance(postfix, str):
                self.setDescriptionField(1, "postfix", postfix)
        
        def message(self, msg:str):
            if isinstance(msg, str):
                self.setInfoMessage(msg)

        def clear(self):
            if self.view:
                self.setError(0)
                self.setInfoMessage("")
                self.__exit__(None, None, None)

        def __enter__(self):
            self.viewPath = self.__class__.server.requestView("tqdm", "", 0)
            self.view = self.__class__.bus.get_object("org.kde.kuiserver", self.viewPath)
            for mn in self.__class__.methodsNames:
                setattr(self, mn, self.view.get_dbus_method(mn, dbus_interface="org.kde.JobViewV2"))
            self.setDescriptionField(0, "tqdm", "")
            self.setInfoMessage("tqdm")
            if self.total:
                self.setTotalAmount(self.total, self.unit)
            return self

        def __exit__(self, exception_type, exception_value, traceback):
            if self.view:
                self.viewPath = None
                self.view = None
                for mn in self.__class__.methodsNames:
                    setattr(self, mn, None)


except:
    from .PlatformSpecificProgressReporter import DummyProgressReporter as DBusProgressReporter
