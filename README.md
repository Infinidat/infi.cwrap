Overview
========

Working with ctypes is hard. specifically, wrapping functions is hard.
this module helps you do that.

Usage
-----

Below is a production code that uses infi.cwrap:

```python
from infi.exceptools import InfiException
from infi.cwrap import WrappedFunction, IN, IN_OUT
from ctypes import c_void_p, c_ulong

class IoctlException(InfiException):
    pass

class WindowsException(IoctlException):
    def __init__(self, errno):
        from ctypes import FormatError
        self.winerror = errno
        self.strerror = FormatError(errno)

    def __repr__(self):
        return "%s, %s" % (self.winerror, self.strerror)

    def __str__(self):
        return self.__repr__()

class InvalidHandle(WindowsException):
    pass

HANDLE = c_void_p
DWORD = c_ulong
BOOL = c_ulong

def errcheck_invalid_handle():
    from .constants import INVALID_HANDLE_VALUE
    from ctypes import GetLastError
    def errcheck(result, func, args):
        if result == INVALID_HANDLE_VALUE:
            last_error = GetLastError()
            raise InvalidHandle(last_error)
        return result
    return errcheck

class CreateFileW(WrappedFunction):
    return_value = HANDLE

    @classmethod
    def get_errcheck(cls):
        return errcheck_invalid_handle()

    @classmethod
    def get_library_name(cls):
        return 'kernel32'

    @classmethod
    def get_parameters(cls):
        return ((c_void_p, IN, "FileName"),
                (DWORD, IN, "DesiredAccess"),
                (DWORD, IN, "SharedMode"),
                (c_void_p, IN, "SecurityAttributes"),
                (DWORD, IN, "CreationDisposition"),
                (DWORD, IN, "FlagsAndAttributes"),
                (HANDLE, IN_OUT, "TemplateFile"))

class CloseHandle(WrappedFunction):
    return_value = BOOL

    @classmethod
    def get_errcheck(cls):
        return errcheck_bool()

    @classmethod
    def get_library_name(cls):
        return 'kernel32'

    @classmethod
    def get_parameters(cls):
       return ((HANDLE, IN, "Device"),)
 
@contextmanager
def open_handle(device_path, open_generic=False, open_shared=True):
    from constants import GENERIC_READ, GENERIC_WRITE, OPEN_EXISTING
    from constants import FILE_SHARE_READ, FILE_SHARE_WRITE, OPEN_EXISTING
    handle = None
    try:
        handle = CreateFileW(ctypes.create_unicode_buffer(device_path),
                             GENERIC_READ | GENERIC_WRITE if open_generic else 0,
                             FILE_SHARE_READ | FILE_SHARE_WRITE if open_shared else 0,
                             0, OPEN_EXISTING, 0, 0)
        yield handle
    finally:
        if handle is not None:
            CloseHandle(handle)
```

And here's we it is being used:

```python
>>> with open_handle(r"\\.\PhysicalDrive1"):
...     pass
```

Checking out the code
=====================

This project uses buildout and infi-projector, and git to generate setup.py and __version__.py.
In order to generate these, first get infi-projector:

    easy_install infi.projector

and then run in the project directory:

    projector devenv build

