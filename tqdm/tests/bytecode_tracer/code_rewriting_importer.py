"""
Custom importer that additionally rewrites code of all imported modules.

Based on Demo/imputil/importers.py file distributed with Python 2.x.
"""

import imp
import imputil
import marshal
import os
import struct
import sys

from types import CodeType

# byte-compiled file suffic character
_suffix_char = __debug__ and 'c' or 'o'

# byte-compiled file suffix
_suffix = '.py' + _suffix_char

# the C_EXTENSION suffixes
_c_suffixes = filter(lambda x: x[2] == imp.C_EXTENSION, imp.get_suffixes())


def _timestamp(pathname):
    "Return the file modification time as a Long."
    try:
        s = os.stat(pathname)
    except OSError:
        return None
    return long(s[8])

def _compile(path):
    "Read and compile Python source code from file."
    f = open(path)
    c = f.read()
    f.close()
    return compile(c, path, 'exec')

def _fs_import(dir, modname, fqname):
    "Fetch a module from the filesystem."

    pathname = os.path.join(dir, modname)
    if os.path.isdir(pathname):
        values = { '__pkgdir__' : pathname, '__path__' : [ pathname ] }
        ispkg = 1
        pathname = os.path.join(pathname, '__init__')
    else:
        values = { }
        ispkg = 0

        # look for dynload modules
        for desc in _c_suffixes:
            file = pathname + desc[0]
            try:
                fp = open(file, desc[1])
            except IOError:
                pass
            else:
                module = imp.load_module(fqname, fp, file, desc)
                values['__file__'] = file
                return 0, module, values

    t_py = _timestamp(pathname + '.py')
    t_pyc = _timestamp(pathname + _suffix)
    if t_py is None and t_pyc is None:
        return None
    code = None
    if t_py is None or (t_pyc is not None and t_pyc >= t_py):
        file = pathname + _suffix
        f = open(file, 'rb')
        if f.read(4) == imp.get_magic():
            t = struct.unpack('<I', f.read(4))[0]
            if t == t_py:
                code = marshal.load(f)
        f.close()
    if code is None:
        file = pathname + '.py'
        code = _compile(file)

    values['__file__'] = file
    return ispkg, code, values

class PathImporter(imputil.Importer):
    def __init__(self, path, callback):
        self.path = path
        self.callback = callback

    def rewrite(self, retvals):
        if isinstance(retvals, tuple) and type(retvals[1]) == CodeType:
            return (retvals[0], self.callback(retvals[1]), retvals[2])
        return retvals

    def get_code(self, parent, modname, fqname):
        if parent:
            # we are looking for a module inside of a specific package
            return self.rewrite(_fs_import(parent.__pkgdir__, modname, fqname))

        # scan sys.path, looking for the requested module
        for dir in self.path:
            if isinstance(dir, str):
                result = _fs_import(dir, modname, fqname)
                if result:
                    return self.rewrite(result)

        # not found
        return None

import_manager = imputil.ImportManager()

def install(callback):
    "Install callback as a code-rewriting function for each imported module."
    import_manager.install()
    sys.path.insert(0, PathImporter(sys.path, callback))

def uninstall():
    import_manager.uninstall()
