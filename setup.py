#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from setuptools import setup

src_dir = os.path.abspath(os.path.dirname(__file__))
if sys.argv[1].lower().strip() == 'make':  # exec Makefile commands
    import pymake
    fpath = os.path.join(src_dir, 'Makefile')
    pymake.main(['-f', fpath] + sys.argv[2:])
    # Stop to avoid setup.py raising non-standard command error
    sys.exit(0)

setup(use_scm_version=True)
