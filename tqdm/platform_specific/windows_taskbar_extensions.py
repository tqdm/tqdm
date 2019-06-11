__all__ = ("WindowsTaskbarProgressReporter",)

import sys

if sys.getwindowsversion() >= (6, 1):
    from enum import IntFlag
    from ctypes import HRESULT, POINTER, c_int, c_ulonglong, c_wchar_p

    import win32con
    import win32gui
    from comtypes import COMMETHOD, GUID, IUnknown
    import comtypes.client
    from win32console import GetConsoleWindow

    from .IProgressReporter import IProgressReporter

    dummyMethod = COMMETHOD([], None, "__dummyMethodDontUse__")

    class Library(object):
        name = "TaskbarLib"
        _reg_typelib_ = ("{683BF642-E9CA-4124-BE43-67065B2FA653}", 1, 0)

    class ITaskbarList(IUnknown):
        _case_insensitive_ = True
        _iid_ = GUID("{56FDF342-FD6D-11D0-958A-006097C9A090}")
        _idlflags_ = []

    class ITaskbarList2(ITaskbarList):
        _case_insensitive_ = True
        _iid_ = GUID("{602D4995-B13A-429B-A66E-1935E44F4317}")
        _idlflags_ = []

    class ITaskbarList3(ITaskbarList2):
        _case_insensitive_ = True
        _iid_ = GUID("{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}")
        _idlflags_ = []

    ITaskbarList._methods_ = [
        dummyMethod,
        dummyMethod,
        dummyMethod,
        dummyMethod,
        dummyMethod,
    ]

    ITaskbarList2._methods_ = [
        dummyMethod,
    ]

    class TBPFlag(IntFlag):
        """See https://docs.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-itaskbarlist3-setprogressstate"""

        noProgress = 0
        indeterminate = 1
        normal = 2
        error = 4
        paused = 8

    ITaskbarList3._methods_ = [
        COMMETHOD(
            [],
            HRESULT,
            "SetProgressValue",
            (["in"], c_int, "hwnd"),
            (["in"], c_ulonglong, "ullCompleted"),
            (["in"], c_ulonglong, "ullTotal"),
        ),
        COMMETHOD(
            [],
            HRESULT,
            "SetProgressState",
            (["in"], c_int, "hwnd"),
            (["in"], c_int, "tbpFlags"),
        ),
        dummyMethod,
        dummyMethod,
        dummyMethod,
        dummyMethod,
        dummyMethod,
        dummyMethod,
        dummyMethod,
        COMMETHOD(
            [],
            HRESULT,
            "SetOverlayIcon",
            (["in"], c_int, "hwnd"),
            (["in"], POINTER(IUnknown), "hIcon"),
            (["in"], c_wchar_p, "pszDescription"),
        ),
        COMMETHOD(
            [],
            HRESULT,
            "SetThumbnailTooltip",
            (["in"], c_int, "hwnd"),
            (["in"], c_wchar_p, "pszTip"),
        ),
        dummyMethod,
    ]

    class iconz:
        """Just a storage for icons"""

        success = win32gui.LoadIcon(None, win32con.IDI_INFORMATION)
        fail = win32gui.LoadIcon(None, win32con.IDI_ERROR)

    class WindowsTaskbarProgressReporter(IProgressReporter):
        """Reports progress using Windows 7+ Taskbar Extensions."""

        __slots__ = ("hwnd", "total")
        taskBarList = None
        taskBarListRefCount = 0

        def __init__(self, total: int = None, unit: str = ""):
            self.hwnd = GetConsoleWindow()
            self.total = total

        def progress(self, current: int, speed: float):
            if self.total:
                self.__class__.taskBarList.SetProgressState(
                    self.hwnd, TBPFlag.normal
                )
                self.__class__.taskBarList.SetProgressValue(
                    self.hwnd, current, self.total
                )
                #self.__class__.taskBarList.SetThumbnailTooltip(self.hwnd, "tqdm: "+str(current)+"/"+str(total))
            else:
                self.__class__.taskBarList.SetProgressState(
                    self.hwnd, TBPFlag.indeterminate
                )
                #self.__class__.taskBarList.SetThumbnailTooltip(self.hwnd, "tqdm: "+str(current))

        def fail(self, reason: str = None):
            self.__class__.taskBarList.SetProgressState(
                self.hwnd, TBPFlag.error
            )
            #self.__class__.taskBarList.SetOverlayIcon(self.hwnd, iconz.fail, "An error occured during tqdmed loop")

        def success(self):
            #self.__class__.taskBarList.SetOverlayIcon(self.hwnd, iconz.success, "tqdm loop succesfully finished")
            self.__class__.taskBarList.SetProgressState(
                self.hwnd, TBPFlag.noProgress
            )

        def clear(self):
            if self.__class__.taskBarList:
                self.__class__.taskBarList.SetProgressState(
                    self.hwnd, TBPFlag.noProgress
                )
                #self.__class__.taskBarList.SetOverlayIcon(self.hwnd, None, None)

        def __enter__(self):
            if not self.__class__.taskBarListRefCount:
                self.__class__.taskBarList = comtypes.client.CreateObject(
                    "{56FDF344-FD6D-11d0-958A-006097C9A090}",
                    interface=ITaskbarList3,
                )
            self.__class__.taskBarListRefCount += 1
            return self

        def __exit__(self, exception_type, exception_value, traceback):
            if self.__class__.taskBarListRefCount > 0:
                self.__class__.taskBarListRefCount -= 1
            if not self.__class__.taskBarListRefCount:
                #self.__class__.taskBarList.Release()
                self.__class__.taskBarList = None


else:
    from .IProgressReporter import (
        DummyProgressReporter as WindowsTaskbarProgressReporter,
    )
