#!/usr/bin/env python
# -*- coding: utf-8 -*-
from io import open as io_open
from setuptools import setup
import os
import sys

# Get version from tqdm/_version.py
__version__ = None
src_dir = os.path.abspath(os.path.dirname(__file__))
version_file = os.path.join(src_dir, 'tqdm', '_version.py')
with io_open(version_file, mode='r') as fd:
    exec(fd.read())

# Executing makefile commands if specified
if sys.argv[1].lower().strip() == 'make':
    import pymake
    # Filename of the makefile
    fpath = os.path.join(src_dir, 'Makefile')
    pymake.main(['-f', fpath] + sys.argv[2:])
    # Stop to avoid setup.py raising non-standard command error
    sys.exit(0)

extras_require = {}
requirements_dev = os.path.join(src_dir, 'requirements-dev.txt')
with io_open(requirements_dev, mode='r') as fd:
    extras_require['dev'] = [i.strip().split('#', 1)[0].strip()
                             for i in fd.read().strip().split('\n')]

setup(version=__version__, extras_require=extras_require)
