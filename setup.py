#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from os import path

from setuptools import setup

src_dir = path.abspath(path.dirname(__file__))
if sys.argv[1].lower().strip() == 'make':  # exec Makefile commands
    import pymake
    fpath = path.join(src_dir, 'Makefile')
    pymake.main(['-f', fpath] + sys.argv[2:])
    # Stop to avoid setup.py raising non-standard command error
    sys.exit(0)

setup(use_scm_version=True)
