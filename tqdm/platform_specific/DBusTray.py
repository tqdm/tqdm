__all__ = ("DBusProgressReporter",)

try:
    from dbus import SessionBus

    from .IProgressReporter import IProgressReporter

    class DBusProgressReporterBaseMeta(IProgressReporter.__class__):
        def __new__(cls, className, parents, attrs, *args, **kwargs):
            parentsMethodsNames = getattr(parents[0], "methodsNames", ()) if parents else ()
            attrs = type(attrs)(attrs)
            mns = attrs.get("methodsNames", ())
            slots = attrs.get("__slots__", None)
            if slots is not None:
                slotsAddition = []
                for mn in mns:
                    if isinstance(mn, tuple):
                        mn, tn = mn
                    else:
                        tn = mn

                    slotsAddition.append(tn)
                    attrs["__slots__"] = slots + tuple(slotsAddition)
            attrs["methodsNames"] = parentsMethodsNames + mns
            return super().__new__(
                cls, className, parents, attrs, *args, **kwargs
            )

    class DBusProgressReporterBase(
        IProgressReporter, metaclass=DBusProgressReporterBaseMeta
    ):
        """Outputs progress using DBus into tray."""

        __slots__ = ("viewPath", "view", "unit", "total", "errorCode", "reason")
        methodsNames = (("terminate", "_terminate"),)
        bus = SessionBus()
        server = bus.get_object("org.kde.kuiserver", "/JobViewServer")
        interfaceName = None

        def processInterfaces(self, f):
            for mn in self.__class__.methodsNames:
                if isinstance(mn, tuple):
                    mn, tn = mn
                else:
                    tn = mn
                f(self, mn, tn)

        def __init__(self, total: int = None, unit: str = "") -> None:
            self.viewPath = None
            self.view = None
            self.unit = unit
            self.total = total
            self.errorCode = 0
            self.reason = ""
            self.processInterfaces(
                lambda sself, mn, tn: setattr(sself, tn, None)
            )

        def terminate(self, code, msg: str, hints):
            self._terminate(msg)

        def progress(self, current: int, speed: float = None) -> None:
            self.setProcessedAmount(current, self.unit)
            self.setPercent(current / self.total * 100)
            if speed is not None:
                self.setSpeed(speed)

        def fail(self, reason: str = "Failed"):
            self.errorCode = 100
            self.reason = reason
            if self.view:
                self.__exit__(None, None, None)

        def success(self) -> None:
            self.errorCode = 0
            self.__exit__(None, None, None)

        def prefix(self, prefix: str) -> None:
            if isinstance(prefix, str):
                self.setDescriptionField(0, "Description:", prefix)

        def postfix(self, postfix: str) -> None:
            if isinstance(postfix, str):
                self.setDescriptionField(1, "postfix", postfix)

        def message(self, msg: str):
            if isinstance(msg, str):
                self.setInfoMessage(msg)

        def clear(self):
            self.errorCode = 0
            self.reason = ""
            if self.view:
                self.__exit__(None, None, None)

        def __enter__(self) -> "DBusProgressReporter":
            self.viewPath = self.__class__.server.requestView("tqdm", "", 0)
            self.view = self.__class__.bus.get_object(
                "org.kde.kuiserver", self.viewPath
            )
            self.processInterfaces(
                lambda sself, mn, tn: setattr(
                    sself,
                    tn,
                    self.view.get_dbus_method(
                        mn, dbus_interface=self.__class__.interfaceName
                    ),
                )
            )
            self.setDescriptionField(0, "tqdm", "")
            self.setInfoMessage("tqdm")
            if self.total:
                self.setTotalAmount(self.total, self.unit)
            return self

        def __exit__(
            self, exception_type: None, exception_value: None, traceback: None
        ) -> None:
            if self.view:
                if self.reason:
                    self.setInfoMessage(self.reason)
                self.terminate(self.errorCode, self.reason, {})
                self.viewPath = None
                self.view = None
                self.processInterfaces(
                    lambda sself, mn, tn: setattr(sself, tn, None)
                )

    class DBusProgressReporterV2(DBusProgressReporterBase):
        """Outputs progress using DBus into tray."""

        methodsNames = (
            "setError",
            "setPercent",
            "setSpeed",
            "setTotalAmount",
            "setProcessedAmount",
            "setDescriptionField",
            "setInfoMessage",
        )
        __slots__ = ()
        interfaceName = "org.kde.JobViewV2"

    DBusProgressReporter = DBusProgressReporterV2

    class DBusProgressReporterV3(DBusProgressReporterBase):
        """Outputs progress using DBus into tray."""

        methodsNames = ("update",)
        __slots__ = ()
        interfaceName = "org.kde.JobViewV3"
        unitRemapping = {
            "items": "items",
            "bytes": "bytes",
            "files": "files",
            "dirs": "directories",
        }

        def terminate(self, *args, **kwargs):
            self._terminate(*args, **kwargs)

        def setDescriptionField(self, iD, label, value):
            iD += 1  # starts from 1
            labelPropName = "descriptionLabel" + str(iD)
            valuePropName = "descriptionValue" + str(iD)
            self.update({labelPropName: label, valuePropName: value})

        def setTitle(self, title: str):
            self.update({"title": title})

        def setDestURL(self, url: str):
            self.update({"destUrl": url})

        def setInfoMessage(self, msg: str):
            self.update({"infoMessage": msg})

        def setPercent(self, value: float):
            self.update({"percent": value})

        def setSpeed(self, value: float):
            self.update({"speed": value})

        def setError(self, msg: str):
            self.update({"error": msg})

        @classmethod
        def _remapUnit(cls, unit: str):
            return cls.unitRemapping.get(unit, "items")

        @classmethod
        def _remapUnitToPropName(cls, prefix: str, unit: str):
            if unit:
                unit = cls._remapUnit(unit)
                unit = unit[0].upper() + unit[1:]
                return prefix + unit
            return prefix

        def setTotalAmount(self, total: int, unit: str):
            self.update(
                {self.__class__._remapUnitToPropName("total", unit): total}
            )

        def setProcessedAmount(self, processed: int, unit: str):
            self.update(
                {
                    self.__class__._remapUnitToPropName(
                        "processed", unit
                    ): processed
                }
            )

    # DBusProgressReporter = DBusProgressReporterV3
    # for now no substantional advantages (v3 may
    # be a bit less overheady in initialization),
    # implements essentially the same functionality
except BaseException:
    from .IProgressReporter import DummyProgressReporter as DBusProgressReporter
