|Logo|

tqdm
====

|PyPI-Status| |PyPI-Versions| |Conda-Forge-Status|

|Build-Status| |Coverage-Status| |Branch-Coverage-Status| |Codacy-Grade|

|DOI-URI| |LICENCE| |OpenHub-Status|


``tqdm`` means "progress" in Arabic (taqadum, تقدّم)
and an abbreviation for "I love you so much" in Spanish (te quiero demasiado).

Instantly make your loops show a smart progress meter - just wrap any
iterable with ``tqdm(iterable)``, and you're done!

.. code:: python

    from tqdm import tqdm
    for i in tqdm(range(10000)):
        ...

``76%|████████████████████████████         | 7568/10000 [00:33<00:10, 229.00it/s]``

``trange(N)`` can be also used as a convenient shortcut for
``tqdm(xrange(N))``.

|Screenshot|
    REPL: `ptpython <https://github.com/jonathanslenders/ptpython>`__

It can also be executed as a module with pipes:

.. code:: sh

    $ seq 9999999 | tqdm --unit_scale | wc -l
    10.0Mit [00:02, 3.58Mit/s]
    9999999
    $ 7z a -bd -r backup.7z docs/ | grep Compressing | \
        tqdm --total $(find docs/ -type f | wc -l) --unit files >> backup.log
    100%|███████████████████████████████▉| 8014/8014 [01:37<00:00, 82.29files/s]

Overhead is low -- about 60ns per iteration (80ns with ``tqdm_gui``), and is
unit tested against performance regression.
By comparison, the well-established
`ProgressBar <https://github.com/niltonvolpato/python-progressbar>`__ has
an 800ns/iter overhead.

In addition to its low overhead, ``tqdm`` uses smart algorithms to predict
the remaining time and to skip unnecessary iteration displays, which allows
for a negligible overhead in most cases.

``tqdm`` works on any platform
(Linux, Windows, Mac, FreeBSD, NetBSD, Solaris/SunOS),
in any console or in a GUI, and is also friendly with IPython/Jupyter notebooks.

``tqdm`` does not require any dependencies (not even ``curses``!), just
Python and an environment supporting ``carriage return \r`` and
``line feed \n`` control characters.

------------------------------------------

.. contents:: Table of contents
   :backlinks: top
   :local:


Installation
------------

Latest PyPI stable release
~~~~~~~~~~~~~~~~~~~~~~~~~~

|PyPI-Status|

.. code:: sh

    pip install tqdm

Latest development release on GitHub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|GitHub-Status| |GitHub-Stars| |GitHub-Commits| |GitHub-Forks|

Pull and install in the current directory:

.. code:: sh

    pip install -e git+https://github.com/tqdm/tqdm.git@master#egg=tqdm

Latest Conda release
~~~~~~~~~~~~~~~~~~~~

|Conda-Forge-Status|

.. code:: sh

    conda install -c conda-forge tqdm


Changelog
---------

The list of all changes is available either on GitHub's Releases:
|GitHub-Status|, on the
`wiki <https://github.com/tqdm/tqdm/wiki/Releases>`__ or on crawlers such as
`allmychanges.com <https://allmychanges.com/p/python/tqdm/>`_.


Usage
-----

``tqdm`` is very versatile and can be used in a number of ways.
The three main ones are given below.

Iterable-based
~~~~~~~~~~~~~~

Wrap ``tqdm()`` around any iterable:

.. code:: python

    text = ""
    for char in tqdm(["a", "b", "c", "d"]):
        text = text + char

``trange(i)`` is a special optimised instance of ``tqdm(range(i))``:

.. code:: python

    for i in trange(100):
        pass

Instantiation outside of the loop allows for manual control over ``tqdm()``:

.. code:: python

    pbar = tqdm(["a", "b", "c", "d"])
    for char in pbar:
        pbar.set_description("Processing %s" % char)

Manual
~~~~~~

Manual control on ``tqdm()`` updates by using a ``with`` statement:

.. code:: python

    with tqdm(total=100) as pbar:
        for i in range(10):
            pbar.update(10)

If the optional variable ``total`` (or an iterable with ``len()``) is
provided, predictive stats are displayed.

``with`` is also optional (you can just assign ``tqdm()`` to a variable,
but in this case don't forget to ``del`` or ``close()`` at the end:

.. code:: python

    pbar = tqdm(total=100)
    for i in range(10):
        pbar.update(10)
    pbar.close()

Module
~~~~~~

Perhaps the most wonderful use of ``tqdm`` is in a script or on the command
line. Simply inserting ``tqdm`` (or ``python -m tqdm``) between pipes will pass
through all ``stdin`` to ``stdout`` while printing progress to ``stderr``.

The example below demonstrated counting the number of lines in all Python files
in the current directory, with timing information included.

.. code:: sh

    $ time find . -name '*.py' -exec cat \{} \; | wc -l
    857365

    real    0m3.458s
    user    0m0.274s
    sys     0m3.325s

    $ time find . -name '*.py' -exec cat \{} \; | tqdm | wc -l
    857366it [00:03, 246471.31it/s]
    857365

    real    0m3.585s
    user    0m0.862s
    sys     0m3.358s

Note that the usual arguments for ``tqdm`` can also be specified.

.. code:: sh

    $ find . -name '*.py' -exec cat \{} \; |
        tqdm --unit loc --unit_scale --total 857366 >> /dev/null
    100%|███████████████████████████████████| 857K/857K [00:04<00:00, 246Kloc/s]

Backing up a large directory?

.. code:: sh

    $ 7z a -bd -r backup.7z docs/ | grep Compressing |
        tqdm --total $(find docs/ -type f | wc -l) --unit files >> backup.log
    100%|███████████████████████████████▉| 8014/8014 [01:37<00:00, 82.29files/s]


FAQ and Known Issues
--------------------

|GitHub-Issues|

The most common issues relate to excessive output on multiple lines, instead
of a neat one-line progress bar.

- Consoles in general: require support for carriage return (``CR``, ``\r``).
- Nested progress bars:
    * Consoles in general: require support for moving cursors up to the
      previous line. For example,
      `IDLE <https://github.com/tqdm/tqdm/issues/191#issuecomment-230168030>`__,
      `ConEmu <https://github.com/tqdm/tqdm/issues/254>`__ and
      `PyCharm <https://github.com/tqdm/tqdm/issues/203>`__ (also
      `here <https://github.com/tqdm/tqdm/issues/208>`__,
      `here <https://github.com/tqdm/tqdm/issues/307>`__, and
      `here <https://github.com/tqdm/tqdm/issues/454#issuecomment-335416815>`__)
      lack full support.
    * Windows: additionally may require the Python module ``colorama``
      to ensure nested bars stay within their respective lines.
- Unicode:
    * Environments which report that they support unicode will have solid smooth
      progressbars. The fallback is an `ascii`-only bar.
    * Windows consoles often only partially support unicode and thus
      `often require explicit ascii=True <https://github.com/tqdm/tqdm/issues/454#issuecomment-335416815>`__
      (also `here <https://github.com/tqdm/tqdm/issues/499>`__). This is due to
      either normal-width unicode characters being incorrectly displayed as
      "wide", or some unicode characters not rendering.
- Wrapping enumerated iterables: use ``enumerate(tqdm(...))`` instead of
  ``tqdm(enumerate(...))``. The same applies to ``numpy.ndenumerate``.
  This is because enumerate functions tend to hide the length of iterables.
  ``tqdm`` does not.
- Wrapping zipped iterables has similar issues due to internal optimisations.
  ``tqdm(zip(a, b))`` should be replaced with ``zip(tqdm(a), b)`` or even
  ``zip(tqdm(a), tqdm(b))``.

If you come across any other difficulties, browse and file |GitHub-Issues|.

Documentation
-------------

|PyPI-Versions| |README-Hits| (Since 19 May 2016)

.. code:: python

    class tqdm(object):
      """
      Decorate an iterable object, returning an iterator which acts exactly
      like the original iterable, but prints a dynamically updating
      progressbar every time a value is requested.
      """

      def __init__(self, iterable=None, desc=None, total=None, leave=True,
                   file=None, ncols=None, mininterval=0.1,
                   maxinterval=10.0, miniters=None, ascii=None, disable=False,
                   unit='it', unit_scale=False, dynamic_ncols=False,
                   smoothing=0.3, bar_format=None, initial=0, position=None,
                   postfix=None):

Parameters
~~~~~~~~~~

* iterable  : iterable, optional  
    Iterable to decorate with a progressbar.
    Leave blank to manually manage the updates.
* desc  : str, optional  
    Prefix for the progressbar.
* total  : int, optional  
    The number of expected iterations. If (default: None),
    len(iterable) is used if possible. As a last resort, only basic
    progress statistics are displayed (no ETA, no progressbar).
    If ``gui`` is True and this parameter needs subsequent updating,
    specify an initial arbitrary large positive integer,
    e.g. int(9e9).
* leave  : bool, optional  
    If [default: True], keeps all traces of the progressbar
    upon termination of iteration.
* file  : ``io.TextIOWrapper`` or ``io.StringIO``, optional  
    Specifies where to output the progress messages
    (default: sys.stderr). Uses ``file.write(str)`` and ``file.flush()``
    methods.
* ncols  : int, optional  
    The width of the entire output message. If specified,
    dynamically resizes the progressbar to stay within this bound.
    If unspecified, attempts to use environment width. The
    fallback is a meter width of 10 and no limit for the counter and
    statistics. If 0, will not print any meter (only stats).
* mininterval  : float, optional  
    Minimum progress display update interval, in seconds [default: 0.1].
* maxinterval  : float, optional  
    Maximum progress display update interval, in seconds [default: 10].
    Automatically adjusts ``miniters`` to correspond to ``mininterval``
    after long display update lag. Only works if ``dynamic_miniters``
    or monitor thread is enabled.
* miniters  : int, optional  
    Minimum progress display update interval, in iterations.
    If 0 and ``dynamic_miniters``, will automatically adjust to equal
    ``mininterval`` (more CPU efficient, good for tight loops).
    If > 0, will skip display of specified number of iterations.
    Tweak this and ``mininterval`` to get very efficient loops.
    If your progress is erratic with both fast and slow iterations
    (network, skipping items, etc) you should set miniters=1.
* ascii  : bool, optional  
    If unspecified or False, use unicode (smooth blocks) to fill
    the meter. The fallback is to use ASCII characters ``1-9 #``.
* disable  : bool, optional  
    Whether to disable the entire progressbar wrapper
    [default: False].
* unit  : str, optional  
    String that will be used to define the unit of each iteration
    [default: it].
* unit_scale  : bool or int or float, optional  
    If 1 or True, the number of iterations will be reduced/scaled
    automatically and a metric prefix following the
    International System of Units standard will be added
    (kilo, mega, etc.) [default: False]. If any other non-zero
    number, will scale `total` and `n`.
* dynamic_ncols  : bool, optional  
    If set, constantly alters ``ncols`` to the environment (allowing
    for window resizes) [default: False].
* smoothing  : float, optional  
    Exponential moving average smoothing factor for speed estimates
    (ignored in GUI mode). Ranges from 0 (average speed) to 1
    (current/instantaneous speed) [default: 0.3].
* bar_format  : str, optional  
    Specify a custom bar string formatting. May impact performance.
    [default: '{l_bar}{bar}{r_bar}'], where
    l_bar='{desc}: {percentage:3.0f}%|' and
    r_bar='| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, '
    '{rate_fmt}{postfix}]'
    Possible vars: l_bar, bar, r_bar, n, n_fmt, total, total_fmt,
    percentage, rate, rate_fmt, rate_noinv, rate_noinv_fmt,
    rate_inv, rate_inv_fmt, elapsed, remaining, desc, postfix.
    Note that a trailing ": " is automatically removed after {desc}
    if the latter is empty.
* initial  : int, optional  
    The initial counter value. Useful when restarting a progress
    bar [default: 0].
* position  : int, optional  
    Specify the line offset to print this bar (starting from 0)
    Automatic if unspecified.
    Useful to manage multiple bars at once (eg, from threads).
* postfix  : dict or ``*``, optional  
    Specify additional stats to display at the end of the bar.
    Calls ``set_postfix(**postfix)`` if possible (dict).
* unit_divisor  : float, optional  
    [default: 1000], ignored unless `unit_scale` is True.

Extra CLI Options
~~~~~~~~~~~~~~~~~

* delim  : chr, optional  
    Delimiting character [default: '\n']. Use '\0' for null.
    N.B.: on Windows systems, Python converts '\n' to '\r\n'.
* buf_size  : int, optional  
    String buffer size in bytes [default: 256]
    used when ``delim`` is specified.
* bytes  : bool, optional  
    If true, will count bytes and ignore ``delim``.

Returns
~~~~~~~

* out  : decorated iterator.

.. code:: python

      def update(self, n=1):
          """
          Manually update the progress bar, useful for streams
          such as reading files.
          E.g.:
          >>> t = tqdm(total=filesize) # Initialise
          >>> for current_buffer in stream:
          ...    ...
          ...    t.update(len(current_buffer))
          >>> t.close()
          The last line is highly recommended, but possibly not necessary if
          ``t.update()`` will be called in such a way that ``filesize`` will be
          exactly reached and printed.

          Parameters
          ----------
          n  : int, optional
              Increment to add to the internal counter of iterations
              [default: 1].
          """

      def close(self):
          """
          Cleanup and (if leave=False) close the progressbar.
          """

      def unpause(self):
          """
          Restart tqdm timer from last print time.
          """

      def clear(self, nomove=False):
          """
          Clear current bar display
          """

      def refresh(self):
          """
          Force refresh the display of this bar
          """

      def write(cls, s, file=sys.stdout, end="\n"):
          """
          Print a message via tqdm (without overlap with bars)
          """

      def set_description(self, desc=None, refresh=True):
          """
          Set/modify description of the progress bar.

          Parameters
          ----------
          desc  : str, optional
          refresh  : bool, optional
              Forces refresh [default: True].
          """

      def set_postfix(self, ordered_dict=None, refresh=True, **kwargs):
          """
          Set/modify postfix (additional stats)
          with automatic formatting based on datatype.

          Parameters
          ----------
          refresh  : bool, optional
              Forces refresh [default: True].
          """

    def trange(*args, **kwargs):
        """
        A shortcut for tqdm(xrange(*args), **kwargs).
        On Python3+ range is used instead of xrange.
        """

    class tqdm_gui(tqdm):
        """
        Experimental GUI version of tqdm!
        """

    def tgrange(*args, **kwargs):
        """
        Experimental GUI version of trange!
        """

    class tqdm_notebook(tqdm):
        """
        Experimental IPython/Jupyter Notebook widget using tqdm!
        """

    def tnrange(*args, **kwargs):
        """
        Experimental IPython/Jupyter Notebook widget using tqdm!
        """


Examples and Advanced Usage
---------------------------

- See the `examples <https://github.com/tqdm/tqdm/tree/master/examples>`__
  folder;
- import the module and run ``help()``, or
- consult the `wiki <https://github.com/tqdm/tqdm/wiki>`__.
    - this has an
      `excellent article <https://github.com/tqdm/tqdm/wiki/How-to-make-a-great-Progress-Bar>`__
      on how to make a **great** progressbar.

Description and additional stats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom information can be displayed and updated dynamically on ``tqdm`` bars
with the ``desc`` and ``postfix`` arguments:

.. code:: python

    from tqdm import trange
    from random import random, randint
    from time import sleep

    with trange(100) as t:
        for i in t:
            # Description will be displayed on the left
            t.set_description('GEN %i' % i)
            # Postfix will be displayed on the right,
            # formatted automatically based on argument's datatype
            t.set_postfix(loss=random(), gen=randint(1,999), str='h',
                          lst=[1, 2])
            sleep(0.1)

    with tqdm(total=10, bar_format="{postfix[0]} {postfix[1][value]:>8.2g}",
              postfix=["Batch", dict(value=0)]) as t:
        for i in range(10):
            sleep(0.1)
            t.postfix[1]["value"] = i / 2
            t.update()

Points to remember when using ``{postfix[...]}`` in the ``bar_format`` string:

- ``postfix`` also needs to be passed as an initial argument in a compatible
  format, and
- ``postfix`` will be auto-converted to a string if it is a ``dict``-like
  object. To prevent this behaviour, insert an extra item into the dictionary
  where the key is not a string.

Nested progress bars
~~~~~~~~~~~~~~~~~~~~

``tqdm`` supports nested progress bars. Here's an example:

.. code:: python

    from tqdm import trange
    from time import sleep

    for i in trange(10, desc='1st loop'):
        for j in trange(5, desc='2nd loop', leave=False):
            for k in trange(100, desc='3nd loop'):
                sleep(0.01)

On Windows `colorama <https://github.com/tartley/colorama>`__ will be used if
available to keep nested bars on their respective lines.

For manual control over positioning (e.g. for multi-threaded use),
you may specify ``position=n`` where ``n=0`` for the outermost bar,
``n=1`` for the next, and so on:

.. code:: python

    from time import sleep
    from tqdm import trange, tqdm
    from multiprocessing import Pool, freeze_support, RLock

    L = list(range(9))

    def progresser(n):
        interval = 0.001 / (n + 2)
        total = 5000
        text = "#{}, est. {:<04.2}s".format(n, interval * total)
        for i in trange(total, desc=text, position=n):
            sleep(interval)

    if __name__ == '__main__':
        freeze_support()  # for Windows support
        p = Pool(len(L),
                 # again, for Windows support
                 initializer=tqdm.set_lock, initargs=(RLock(),))
        p.map(progresser, L)
        print("\n" * (len(L) - 2))

Hooks and callbacks
~~~~~~~~~~~~~~~~~~~

``tqdm`` can easily support callbacks/hooks and manual updates.
Here's an example with ``urllib``:

**urllib.urlretrieve documentation**

    | [...]
    | If present, the hook function will be called once
    | on establishment of the network connection and once after each block read
    | thereafter. The hook will be passed three arguments; a count of blocks
    | transferred so far, a block size in bytes, and the total size of the file.
    | [...]

.. code:: python

    import urllib, os
    from tqdm import tqdm

    class TqdmUpTo(tqdm):
        """Provides `update_to(n)` which uses `tqdm.update(delta_n)`."""
        def update_to(self, b=1, bsize=1, tsize=None):
            """
            b  : int, optional
                Number of blocks transferred so far [default: 1].
            bsize  : int, optional
                Size of each block (in tqdm units) [default: 1].
            tsize  : int, optional
                Total size (in tqdm units). If [default: None] remains unchanged.
            """
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)  # will also set self.n = b * bsize

    eg_link = "https://caspersci.uk.to/matryoshka.zip"
    with TqdmUpTo(unit='B', unit_scale=True, miniters=1,
                  desc=eg_link.split('/')[-1]) as t:  # all optional kwargs
        urllib.urlretrieve(eg_link, filename=os.devnull,
                           reporthook=t.update_to, data=None)

Inspired by `twine#242 <https://github.com/pypa/twine/pull/242>`__.
Functional alternative in
`examples/tqdm_wget.py <https://github.com/tqdm/tqdm/blob/master/examples/tqdm_wget.py>`__.

It is recommend to use ``miniters=1`` whenever there is potentially
large differences in iteration speed (e.g. downloading a file over
a patchy connection).

Pandas Integration
~~~~~~~~~~~~~~~~~~

Due to popular demand we've added support for ``pandas`` -- here's an example
for ``DataFrame.progress_apply`` and ``DataFrameGroupBy.progress_apply``:

.. code:: python

    import pandas as pd
    import numpy as np
    from tqdm import tqdm

    df = pd.DataFrame(np.random.randint(0, 100, (100000, 6)))

    # Register `pandas.progress_apply` and `pandas.Series.map_apply` with `tqdm`
    # (can use `tqdm_gui`, `tqdm_notebook`, optional kwargs, etc.)
    tqdm.pandas(desc="my bar!")

    # Now you can use `progress_apply` instead of `apply`
    # and `progress_map` instead of `map`
    df.progress_apply(lambda x: x**2)
    # can also groupby:
    # df.groupby(0).progress_apply(lambda x: x**2)

In case you're interested in how this works (and how to modify it for your
own callbacks), see the
`examples <https://github.com/tqdm/tqdm/tree/master/examples>`__
folder or import the module and run ``help()``.

IPython/Jupyter Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IPython/Jupyter is supported via the ``tqdm_notebook`` submodule:

.. code:: python

    from tqdm import tnrange, tqdm_notebook
    from time import sleep

    for i in tnrange(10, desc='1st loop'):
        for j in tqdm_notebook(xrange(100), desc='2nd loop'):
            sleep(0.01)

In addition to ``tqdm`` features, the submodule provides a native Jupyter
widget (compatible with IPython v1-v4 and Jupyter), fully working nested bars
and color hints (blue: normal, green: completed, red: error/interrupt,
light blue: no ETA); as demonstrated below.

|Screenshot-Jupyter1|
|Screenshot-Jupyter2|
|Screenshot-Jupyter3|

Writing messages
~~~~~~~~~~~~~~~~

Since ``tqdm`` uses a simple printing mechanism to display progress bars,
you should not write any message in the terminal using ``print()`` while
a progressbar is open.

To write messages in the terminal without any collision with ``tqdm`` bar
display, a ``.write()`` method is provided:

.. code:: python

    from tqdm import tqdm, trange
    from time import sleep

    bar = trange(10)
    for i in bar:
        # Print using tqdm class method .write()
        sleep(0.1)
        if not (i % 3):
            tqdm.write("Done task %i" % i)
        # Can also use bar.write()

By default, this will print to standard output ``sys.stdout``. but you can
specify any file-like object using the ``file`` argument. For example, this
can be used to redirect the messages writing to a log file or class.

Redirecting writing
~~~~~~~~~~~~~~~~~~~

If using a library that can print messages to the console, editing the library
by  replacing ``print()`` with ``tqdm.write()`` may not be desirable.
In that case, redirecting ``sys.stdout`` to ``tqdm.write()`` is an option.

To redirect ``sys.stdout``, create a file-like class that will write
any input string to ``tqdm.write()``, and supply the arguments
``file=sys.stdout, dynamic_ncols=True``.

A reusable canonical example is given below:

.. code:: python

    from time import sleep
    import contextlib
    import sys
    from tqdm import tqdm

    class DummyTqdmFile(object):
        """Dummy file-like that will write to tqdm"""
        file = None
        def __init__(self, file):
            self.file = file

        def write(self, x):
            # Avoid print() second call (useless \n)
            if len(x.rstrip()) > 0:
                tqdm.write(x, file=self.file)

        def flush(self):
            return getattr(self.file, "flush", lambda: None)()

    @contextlib.contextmanager
    def std_out_err_redirect_tqdm():
        orig_out_err = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
            yield orig_out_err[0]
        # Relay exceptions
        except Exception as exc:
            raise exc
        # Always restore sys.stdout/err if necessary
        finally:
            sys.stdout, sys.stderr = orig_out_err

    def some_fun(i):
        print("Fee, fi, fo,".split()[i])

    # Redirect stdout to tqdm.write() (don't forget the `as save_stdout`)
    with std_out_err_redirect_tqdm() as orig_stdout:
        # tqdm needs the original stdout
        # and dynamic_ncols=True to autodetect console width
        for i in tqdm(range(3), file=orig_stdout, dynamic_ncols=True):
            sleep(.5)
            some_fun(i)

    # After the `with`, printing is restored
    print("Done!")

Monitoring thread, intervals and miniters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``tqdm`` implements a few tricks to to increase efficiency and reduce overhead.

- Avoid unnecessary frequent bar refreshing: ``mininterval`` defines how long
  to wait between each refresh. ``tqdm`` always gets updated in the background,
  but it will diplay only every ``mininterval``.
- Reduce number of calls to check system clock/time.
- ``mininterval`` is more intuitive to configure than ``miniters``.
  A clever adjustment system ``dynamic_miniters`` will automatically adjust
  ``miniters`` to the amount of iterations that fit into time ``mininterval``.
  Essentially, ``tqdm`` will check if it's time to print without actually
  checking time. This behaviour can be still be bypassed by manually setting
  ``miniters``.

However, consider a case with a combination of fast and slow iterations.
After a few fast iterations, ``dynamic_miniters`` will set ``miniters`` to a
large number. When iteration rate subsequently slows, ``miniters`` will
remain large and thus reduce display update frequency. To address this:

- ``maxinterval`` defines the maximum time between display refreshes.
  A concurrent monitoring thread checks for overdue updates and forces one
  where necessary.

The monitoring thread should not have a noticeable overhead, and guarantees
updates at least every 10 seconds by default.
This value can be directly changed by setting the ``monitor_interval`` of
any ``tqdm`` instance (i.e. ``t = tqdm.tqdm(...); t.monitor_interval = 2``).
The monitor thread may be disabled application-wide by setting
``tqdm.tqdm.monitor_interval = 0`` before instantiatiation of any ``tqdm`` bar.


Contributions
-------------

|GitHub-Commits| |GitHub-Issues| |GitHub-PRs| |OpenHub-Status|

All source code is hosted on `GitHub <https://github.com/tqdm/tqdm>`__.
Contributions are welcome.

See the
`CONTRIBUTING <https://raw.githubusercontent.com/tqdm/tqdm/master/CONTRIBUTING.md>`__
file for more information.


LICENCE
-------

Open Source (OSI approved): |LICENCE|

Citation information: |DOI-URI|


Authors
-------

The main developers, ranked by surviving lines of code, are:

- Casper da Costa-Luis (`casperdcl <https://github.com/casperdcl>`__, ~2/3, |Gift-Casper|)
- Stephen Larroque (`lrq3000 <https://github.com/lrq3000>`__, ~1/3)
- Guangshuo Chen (`chengs <https://github.com/chengs>`__, ~1%)
- Hadrien Mary (`hadim <https://github.com/hadim>`__, ~1%)
- Noam Yorav-Raphael (`noamraph <https://github.com/noamraph>`__, ~1%, original author)
- Mikhail Korobov (`kmike <https://github.com/kmike>`__, ~1%)

There are also many |GitHub-Contributions| which we are grateful for.

|README-Hits| (Since 19 May 2016)

.. |Logo| image:: https://raw.githubusercontent.com/tqdm/tqdm/master/images/logo.gif
.. |Screenshot| image:: https://raw.githubusercontent.com/tqdm/tqdm/master/images/tqdm.gif
.. |Build-Status| image:: https://travis-ci.org/tqdm/tqdm.svg?branch=master
   :target: https://travis-ci.org/tqdm/tqdm
.. |Coverage-Status| image:: https://coveralls.io/repos/tqdm/tqdm/badge.svg?branch=master
   :target: https://coveralls.io/github/tqdm/tqdm
.. |Branch-Coverage-Status| image:: https://codecov.io/gh/tqdm/tqdm/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/tqdm/tqdm
.. |Codacy-Grade| image:: https://api.codacy.com/project/badge/Grade/3f965571598f44549c7818f29cdcf177
   :target: https://www.codacy.com/app/tqdm/tqdm?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=tqdm/tqdm&amp;utm_campaign=Badge_Grade
.. |GitHub-Status| image:: https://img.shields.io/github/tag/tqdm/tqdm.svg?maxAge=86400
   :target: https://github.com/tqdm/tqdm/releases
.. |GitHub-Forks| image:: https://img.shields.io/github/forks/tqdm/tqdm.svg
   :target: https://github.com/tqdm/tqdm/network
.. |GitHub-Stars| image:: https://img.shields.io/github/stars/tqdm/tqdm.svg
   :target: https://github.com/tqdm/tqdm/stargazers
.. |GitHub-Commits| image:: https://img.shields.io/github/commit-activity/y/tqdm/tqdm.svg
   :target: https://github.com/tqdm/tqdm/graphs/commit-activity
.. |GitHub-Issues| image:: https://img.shields.io/github/issues-closed/tqdm/tqdm.svg
   :target: https://github.com/tqdm/tqdm/issues
.. |GitHub-PRs| image:: https://img.shields.io/github/issues-pr-closed/tqdm/tqdm.svg
   :target: https://github.com/tqdm/tqdm/pulls
.. |GitHub-Contributions| image:: https://img.shields.io/github/contributors/tqdm/tqdm.svg
   :target: https://github.com/tqdm/tqdm/graphs/contributors
.. |Gift-Casper| image:: https://img.shields.io/badge/gift-donate-ff69b4.svg
   :target: https://caspersci.uk.to/donate.html
.. |PyPI-Status| image:: https://img.shields.io/pypi/v/tqdm.svg
   :target: https://pypi.python.org/pypi/tqdm
.. |PyPI-Downloads| image:: https://img.shields.io/pypi/dm/tqdm.svg
   :target: https://pypi.python.org/pypi/tqdm
.. |PyPI-Versions| image:: https://img.shields.io/pypi/pyversions/tqdm.svg
   :target: https://pypi.python.org/pypi/tqdm
.. |Conda-Forge-Status| image:: https://anaconda.org/conda-forge/tqdm/badges/version.svg
   :target: https://anaconda.org/conda-forge/tqdm
.. |OpenHub-Status| image:: https://www.openhub.net/p/tqdm/widgets/project_thin_badge?format=gif
   :target: https://www.openhub.net/p/tqdm?ref=Thin+badge
.. |LICENCE| image:: https://img.shields.io/pypi/l/tqdm.svg
   :target: https://raw.githubusercontent.com/tqdm/tqdm/master/LICENCE
.. |DOI-URI| image:: https://zenodo.org/badge/21637/tqdm/tqdm.svg
   :target: https://zenodo.org/badge/latestdoi/21637/tqdm/tqdm
.. |Screenshot-Jupyter1| image:: https://raw.githubusercontent.com/tqdm/tqdm/master/images/tqdm-jupyter-1.gif
.. |Screenshot-Jupyter2| image:: https://raw.githubusercontent.com/tqdm/tqdm/master/images/tqdm-jupyter-2.gif
.. |Screenshot-Jupyter3| image:: https://raw.githubusercontent.com/tqdm/tqdm/master/images/tqdm-jupyter-3.gif
.. |README-Hits| image:: https://caspersci.uk.to/cgi-bin/hits.cgi?q=tqdm&style=social&r=https://github.com/tqdm/tqdm&l=https://caspersci.uk.to/images/tqdm.png&f=https://raw.githubusercontent.com/tqdm/tqdm/master/images/logo.gif
   :target: https://caspersci.uk.to/cgi-bin/hits.cgi?q=tqdm&a=plot&r=https://github.com/tqdm/tqdm&l=https://caspersci.uk.to/images/tqdm.png&f=https://raw.githubusercontent.com/tqdm/tqdm/master/images/logo.gif&style=social
