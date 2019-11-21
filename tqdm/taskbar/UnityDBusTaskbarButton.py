__all__ = ("UnityTaskbarButtonDBusProgressReporter",)

try:
    from .PlatformSpecificProgressReporter import PlatformSpecificProgressReporter
    import psutil
    import os
    from pathlib import Path
    from configparser import ConfigParser
    import re

    import dbus
    from dbus import SessionBus
    import dbus.lowlevel

    def processChain(pid=None):
        """Goes from children to parent, until reaches the process with pid 0"""
        pid = None
        if pid is None:
            pid = os.getpid()
        while pid:
            try:
                proc = psutil.Process(pid)
            except BaseException:
                return
            pn = proc.name()
            yield pn
            pid = proc.ppid()

    incorrectCharactersDBusPath = re.compile(r"[^\w\.]")
    sanRx = re.compile("%\\w")
    menuPaths = (Path("~/.local/share/applications"), Path("/usr/local/share/applications"), Path("/usr/share/applications"))

    def getProcessNameToDesktopFileMapping():
        """Creates a dict mapping process name to .desktop file. It is incorrect way to do it. The correct way is to extract shit from desktop environment memory by using some API, though I have not found any"""
        res = {}
        for el in menuPaths:
            for f in el.glob("**/*.desktop"):
                # print(f)
                t = f.read_text()
                p = ConfigParser(strict=False)
                p.read_string(sanRx.subn("", t)[0])
                p = dict(p)  # in doesn't work on it, seems to be a bug in ConfigParser ...
                if "Desktop Entry" in p:
                    d = dict(p["Desktop Entry"])
                    if "exec" in d:
                        res[Path(d["exec"].split(" ")[0]).name] = f
        return res

    exeName2DesktopMapping = getProcessNameToDesktopFileMapping()
    del menuPaths
    del sanRx

    def getDesktopFileStem(pid=None):
        """Unity (and compatible desktops) use .desktop file name used to start an app for its path in DBus. Without such a file, there will be no progressbar in apps's taskbar button"""
        for pn in processChain(pid):
            if pn in exeName2DesktopMapping:
                return exeName2DesktopMapping[pn].stem

    desktopFileStem = getDesktopFileStem()
    del exeName2DesktopMapping
    if desktopFileStem:

        class UnityTaskbarButtonDBusProgressReporter(PlatformSpecificProgressReporter):
            __slots__ = "total"
            bus = SessionBus()
            interfaceName = "com.canonical.Unity.LauncherEntry"
            methodName = "Update"
            dbusPath = "/".join(("", *incorrectCharactersDBusPath.subn("_", desktopFileStem)[0].split("."), "UnityLauncher"))
            applicationURI = "application://" + desktopFileStem

            def updateViaDBus(self, *, progress: float = None, progressVisible: bool = None, count: int = None, countVisible: bool = None, urgent: bool = None):
                d = dbus.Dictionary()

                if progress is not None:
                    d["progress"] = dbus.Double(progress, variant_level=1)

                if progressVisible is not None:
                    d["progress-visible"] = dbus.Boolean(progressVisible, variant_level=1)

                if count is not None:
                    d["count"] = dbus.Int64(count, variant_level=1)

                if countVisible is not None:
                    d["count-visible"] = dbus.Boolean(countVisible, variant_level=1)

                if urgent is not None:
                    d["urgent"] = dbus.Boolean(urgent, variant_level=1)

                message = dbus.lowlevel.SignalMessage(self.__class__.dbusPath, self.__class__.interfaceName, self.__class__.methodName)
                message.append(self.__class__.applicationURI, d, signature=None)
                self.__class__.bus.send_message(message)

            def __init__(self, total: int = None, unit: str = ""):
                self.total = total

            def progress(self, current: int, speed: float = None):
                self.updateViaDBus(progress=current / self.total, count=current)

            def fail(self, reason:str=None):
                self.updateViaDBus(progress=0, count=0, progressVisible=False, countVisible=False, urgent=True)

            def success(self):
                self.updateViaDBus(progress=100.0, progressVisible=False, countVisible=False)

            def clear(self):
                self.updateViaDBus(progressVisible=False, countVisible=False)

            def __enter__(self):
                self.updateViaDBus(progress=0.0, progressVisible=True, countVisible=True)
                return self

            def __exit__(self, exception_type, exception_value, traceback):
                self.updateViaDBus(progressVisible=False, countVisible=False)
                self.clear()

        del desktopFileStem
    else:
        raise NotImplementedError("There is no .desktop file for this process")

except BaseException:
    from .PlatformSpecificProgressReporter import DummyProgressReporter as UnityTaskbarButtonDBusProgressReporter
