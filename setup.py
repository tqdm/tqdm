#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys
import subprocess
# For Makefile parsing
import shlex
try:  # pragma: no cover
    import ConfigParser
    import StringIO
except ImportError:  # pragma: no cover
    # Python 3 compatibility
    import configparser as ConfigParser
    import io as StringIO
import io
import re


""" Makefile auxiliary functions """


RE_MAKE_CMD = re.compile('^\t(@\+?)(make)?', flags=re.M)


def parse_makefile_aliases(filepath):
    '''
    Parse a makefile to find commands and substitute variables. Expects a
    makefile with only aliases and a line return between each command.

    Returns a dict, with a list of commands for each alias.
    '''

    # -- Parsing the Makefile using ConfigParser
    # Adding a fake section to make the Makefile a valid Ini file
    ini_str = '[root]\n'
    with io.open(filepath, mode='r') as fd:
        ini_str = ini_str + RE_MAKE_CMD.sub('\t', fd.read())
    ini_fp = StringIO.StringIO(ini_str)
    # Parse using ConfigParser
    config = ConfigParser.RawConfigParser()
    config.readfp(ini_fp)
    # Fetch the list of aliases
    aliases = config.options('root')

    # -- Extracting commands for each alias
    commands = {}
    for alias in aliases:
        if alias.lower() in ['.phony']:
            continue
        # strip the first line return, and then split by any line return
        commands[alias] = config.get('root', alias).lstrip('\n').split('\n')

    # -- Commands substitution
    # Loop until all aliases are substituted by their commands:
    # Check each command of each alias, and if there is one command that is to
    # be substituted by an alias, try to do it right away. If this is not
    # possible because this alias itself points to other aliases , then stop
    # and put the current alias back in the queue to be processed again later.

    # Create the queue of aliases to process
    aliases_todo = list(commands.keys())
    # Create the dict that will hold the full commands
    commands_new = {}
    # Loop until we have processed all aliases
    while aliases_todo:
        # Pick the first alias in the queue
        alias = aliases_todo.pop(0)
        # Create a new entry in the resulting dict
        commands_new[alias] = []
        # For each command of this alias
        for cmd in commands[alias]:
            # Ignore self-referencing (alias points to itself)
            if cmd == alias:
                pass
            # Substitute full command
            elif cmd in aliases and cmd in commands_new:
                # Append all the commands referenced by the alias
                commands_new[alias].extend(commands_new[cmd])
            # Delay substituting another alias, waiting for the other alias to
            # be substituted first
            elif cmd in aliases and cmd not in commands_new:
                # Delete the current entry to avoid other aliases
                # to reference this one wrongly (as it is empty)
                del commands_new[alias]
                aliases_todo.append(alias)
                break
            # Full command (no aliases)
            else:
                commands_new[alias].append(cmd)
    commands = commands_new
    del commands_new

    # -- Prepending prefix to avoid conflicts with standard setup.py commands
    # for alias in commands.keys():
    #     commands['make_'+alias] = commands[alias]
    #     del commands[alias]

    return commands


def execute_makefile_commands(commands, alias, verbose=False):
    cmds = commands[alias]
    for cmd in cmds:
        # Parse string in a shell-like fashion
        # (incl quoted strings and comments)
        parsed_cmd = shlex.split(cmd, comments=True)
        # Execute command if not empty (ie, not just a comment)
        if parsed_cmd:
            if verbose:
                print("Running command: " + cmd)
            # Launch the command and wait to finish (synchronized call)
            subprocess.check_call(parsed_cmd)


""" Main setup.py config """


# Get version from tqdm/_version.py
__version__ = None
version_file = os.path.join(os.path.dirname(__file__), 'tqdm', '_version.py')
with io.open(version_file, mode='r') as fd:
    exec(fd.read())

# Executing makefile commands if specified
if sys.argv[1].lower().strip() == 'make':
    # Filename of the makefile
    fpath = 'Makefile'
    # Parse the makefile, substitute the aliases and extract the commands
    commands = parse_makefile_aliases(fpath)

    # If no alias (only `python setup.py make`), print the list of aliases
    if len(sys.argv) < 3 or sys.argv[-1] == '--help':
        print("Shortcut to use commands via aliases. List of aliases:")
        print('\n'.join(alias for alias in sorted(commands.keys())))

    # Else process the commands for this alias
    else:
        arg = sys.argv[-1]
        # if unit testing, we do nothing (we just checked the makefile parsing)
        if arg == 'none':
            sys.exit(0)
        # else if the alias exists, we execute its commands
        elif arg in commands.keys():
            execute_makefile_commands(commands, arg, verbose=True)
        # else the alias cannot be found
        else:
            raise Exception("Provided alias cannot be found: make " + arg)
    # Stop the processing of setup.py here:
    # It's important to avoid setup.py raising an error because of the command
    # not being standard
    sys.exit(0)


""" Python package config """


README_rst = ''
with io.open('README.rst', mode='r', encoding='utf-8') as fd:
    README_rst = fd.read()

setup(
    name='tqdm',
    version=__version__,
    description='A Fast, Extensible Progress Meter',
    license='MPLv2.0, MIT Licenses',
    author='Noam Yorav-Raphael',
    author_email='noamraph@gmail.com',
    url='https://github.com/tqdm/tqdm',
    maintainer='tqdm developers',
    maintainer_email='python.tqdm@gmail.com',
    platforms=['any'],
    packages=['tqdm'],
    entry_points={'console_scripts': ['tqdm=tqdm._main:main'], },
    long_description=README_rst,
    classifiers=[
        # Trove classifiers
        # (https://pypi.python.org/pypi?%3Aaction=list_classifiers)
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Framework :: IPython',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Operating System :: POSIX :: SunOS/Solaris',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: IronPython',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: System :: Monitoring',
        'Topic :: Terminals',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
    ],
    keywords='progressbar progressmeter progress bar meter'
             ' rate eta console terminal time',
    test_suite='nose.collector',
    tests_require=['nose', 'flake8', 'coverage'],
)
