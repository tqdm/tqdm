#!/usr/bin/env python
# -*- coding: utf-8 -*-
from io import open as io_open
from setuptools import setup
import os
import sys

src_dir = os.path.abspath(os.path.dirname(__file__))
if sys.argv[1].lower().strip() == 'make':  # exec Makefile commands
    import pymake
    fpath = os.path.join(src_dir, 'Makefile')
    pymake.main(['-f', fpath] + sys.argv[2:])
    # Stop to avoid setup.py raising non-standard command error
    sys.exit(0)

extras_require = {}
requirements_dev = os.path.join(src_dir, 'requirements-dev.txt')
with io_open(requirements_dev, mode='r') as fd:
    extras_require['dev'] = [i.strip().split('#', 1)[0].strip()
                             for i in fd.read().strip().split('\n')]

setup(use_scm_version=True, extras_require=extras_require)
