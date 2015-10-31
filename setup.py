#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup

# For Makefile parsing
try:    # pragma: no cover
    import ConfigParser
    import StringIO
except ImportError:    # pragma: no cover
    # Python 3 compatibility
    import configparser as ConfigParser
    import io as StringIO
import sys, subprocess


### Makefile auxiliary functions ###


def parse_makefile_aliases(filepath):
    '''Parse a makefile to find commands and substitute variables.
    Note that this function is not a total replacement of make, it only
    parse aliases.
    Expects a makefile with only aliases and ALWAYS a line return between
    each command, eg:

    ```
    all:
        test
        install
    test:
        nosetest
    install:
        python setup.py install
    ```

    Returns a dict, with a list of commands for each alias.
    '''

    # -- Parsing the Makefile using ConfigParser
    # Adding a fake section to make the Makefile a valid Ini file
    ini_str = '[root]\n' + open(filepath, 'r').read()
    ini_fp = StringIO.StringIO(ini_str.replace('@make ',''))
    # Parse it using ConfigParser
    config = ConfigParser.RawConfigParser()
    config.readfp(ini_fp)
    # Fetch the list of aliases
    aliases = config.options('root')

    # -- Extracting commands for each alias
    commands = {}
    for alias in aliases:
        # strip the first line return, and then split by any line return
        commands[alias] = config.get('root', alias).lstrip('\n').split('\n')

    # -- Commands substitution
    # We loop until we can substitute all aliases by their commands
    # What we do is that we check each command of each alias, and
    # if there is one command that is to be substituted by an alias,
    # we try to do it right away, but if it's not possible because
    # this alias himself points to other aliases, then we stop
    # and put the current alias back in the queue, which we
    # will process again later when we have substituted the
    # other aliases.

    # Create the queue of aliases to process
    aliases_todo = commands.keys()
    # Create the dict that will hold the substituted aliases by their full commands
    commands_new = {}
    # Loop until we have processed all aliases
    while aliases_todo:
        # Pick the first alias in the queue
        alias = aliases_todo.pop(0)
        # Create a new entry in the resulting dict
        commands_new[alias] = []
        # For each command of this alias
        for cmd in commands[alias]:
            # If the alias points to itself, we pass
            if cmd == alias:
                pass
            # If the alias points to a full command, we substitute
            elif cmd in aliases and cmd in commands_new:
                # Append all the commands referenced by the alias
                commands_new[alias].extend(commands_new[cmd])
            # If the alias points to another alias, we delay,
            # waiting for the other alias to be substituted first
            elif cmd in aliases and cmd not in commands_new:
                # Delete the current entry to avoid other aliases
                # to reference this one wrongly (as it is empty)
                del commands_new[alias]
                # Put back into the queue
                aliases_todo.append(alias)
                # Break the loop for the current alias
                break
            # Else this is just a full command (no reference to an alias)
            # so we just append it
            else:
                commands_new[alias].append(cmd)
    commands = commands_new
    del commands_new
    # -- Prepending prefix to avoid conflicts with standard setup.py commands
    #for alias in commands.keys():
        #commands['make_'+alias] = commands[alias]
        #del commands[alias]
    return commands

def execute_makefile_commands(commands, alias, verbose=False):
    cmds = commands[alias]
    for cmd in cmds:
        if verbose: print("Running command: %s" % cmd)
        subprocess.check_call(cmd.split())


### Main setup.py config ###


# Get version from tqdm/_version.py
__version__ = None
version_file = os.path.join(os.path.dirname(__file__), 'tqdm', '_version.py')
for line in open(version_file).readlines():
    if (line.startswith('version_info') or line.startswith('__version__')):
        exec(line.strip())

# Executing makefile commands if specified
if sys.argv[1].lower().strip() == 'make':
    # Filename of the makefile
    fpath = 'Makefile'
    # Parse the makefile, substitute the aliases and extract the commands
    commands = parse_makefile_aliases(fpath)

    # If no alias (only `python setup.py make`), print the list of aliases
    if len(sys.argv) < 3 or sys.argv[-1] == '--help':
        print("Shortcut to use commands via aliases. List of aliases:")
        for alias in sorted(commands.keys()):
            print("- "+alias)

    # Else process the commands for this alias
    else:
        arg = sys.argv[-1]
        if arg == 'none': # unit testing, we do nothing (we just checked the makefile parsing)
            sys.exit(0)
        elif arg in commands.keys(): # else if the alias exists, we execute its commands
            execute_makefile_commands(commands, arg, verbose=True)
        else: # else the alias cannot be found
            raise Exception("Provided alias cannot be found: make %s" % (arg))
    # Stop the processing of setup.py here
    sys.exit(0) # Important to avoid setup.py to spit an error because of the command not being standard

# Python package config
setup(
    name='tqdm',
    version=__version__,
    description='A Fast, Extensible Progress Meter',
    license='MIT License',
    author='Noam Yorav-Raphael',
    author_email='noamraph@gmail.com',
    url='https://github.com/tqdm/tqdm',
    maintainer='tqdm developers',
    maintainer_email='python.tqdm@gmail.com',
    platforms = ["any"],
    packages=['tqdm'],
    long_description = open("README.rst", "r").read(),
    classifiers=[  # Trove classifiers, see https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Framework :: IPython',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: System :: Monitoring',
        'Topic :: Terminals',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
    ],
    keywords = 'progressbar progressmeter progress bar meter rate eta console terminal time',
    test_suite='nose.collector',
    tests_require=['nose', 'flake8', 'coverage'],
)
