![Logo](logo.png)

# tqdm

[![Build Status](https://travis-ci.org/tqdm/tqdm.svg?branch=master)](https://travis-ci.org/tqdm/tqdm)
[![Coverage Status](https://coveralls.io/repos/tqdm/tqdm/badge.svg)](https://coveralls.io/r/tqdm/tqdm)

tqdm (read ta<i>qa</i>dum, تقدّم) means "progress" in arabic.

Instantly make your loops show a progress meter - just wrap any iterable with
"tqdm(iterable)", and you're done! Here's what the output looks like:

 76%|████████████████████` ` ` ` ` ` | 7641/10000 [00:34<00:10, 222.22 it/s]

You can also use `trange(N)` as a shortcut for `tqdm(xrange(N))`

![Screenshot](tqdm.gif)

Overhead is low -- about 55ns per iteration. By comparison, our esteemed
competition, [ProgressBar](https://code.google.com/p/python-progressbar/), has
an 878ns/iter overhead. It's a matter of taste, but we also like to think our
version is much more visually appealing.

## Installation

```sh
pip install tqdm
# or
pip install -e git+https://github.com/tqdm/tqdm.git#egg=master
```

## Documentation

```python
class tqdm:

    def __init__(self, iterable=None, desc=None, total=None, leave=False, file=sys.stderr,
         ncols=None, mininterval=0.1, miniters=None, unit=None, unit_scale=False,
         ascii=None, disable=False):
    """
    Decorate an iterable object, returning an iterator which acts exactly
    like the orignal iterable, but prints a dynamically updating
    progressbar.

    Parameters
    ----------
    iterable  : iterable
        Iterable to decorate with a progressbar. You can leave
        it to None if you want to manually manage the updates.
    desc  : str, optional
        Prefix for the progressbar.
    total  : int, optional
        The number of expected iterations. If not given, len(iterable) is
        used if possible. As a last resort, only basic progress statistics
        are displayed.
    file  : `io.TextIOWrapper` or `io.StringIO`, optional
        Specifies where to output the progress messages.
        Uses file.write(str) and file.flush() methods.
    leave  : bool, optional
        if unset, removes all traces of the progressbar upon termination of
        iteration [default: False].
    ncols  : int, optional
        The width of the entire output message. If specified, dynamically
        resizes the progress meter to stay within this bound [default: None].
        The fallback meter width is 10 for the progress bar + no limit for
        the iterations counter and statistics.
    mininterval  : float, optional
        Minimum progress update interval, in seconds [default: 0.1].
    miniters  : int, optional
        Minimum progress update interval, in iterations [default: None].
    unit  : str, optional
        String that will be used to define the unit of each iteration.
        [default: "it"]
    unit_scale  : bool, optional
        If set, the number of iterations will be reduced/scaled automatically
        and a metric prefix following the International System of Units standard
        will be added (kilo, mega, etc.). [default: False]
    ascii  : bool, optional
        If not set, use unicode (▏▎▋█ █) to fill the meter
        [default: False]. The fallback is to use ASCII characters (1-9 #).
    disable : bool
        Disable the progress bar if True [default: False].

    Returns
    -------
    out  : decorated iterator or just a progressbar manager.
    """

    def update(self, n=1):
        """
        Manually update the progress bar, useful for streams such as reading files (set init(total=filesize) and then in the reading loop, use update(len(current_buffer)) )

        Parameters
        ----------
        n  : int
            Increment to add to the internal counter of iterations.
        """

    def close(self):
        """
        Call this method to force print the last progress bar update based on the latest n value
        """

def trange(*args, **kwargs):
    """
    A shortcut for tqdm(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
```

## Contributions

To run the testing suite please make sure tox (http://tox.testrun.org/)
is installed, then type `tox` from the command line.

Alternatively if you don't want to use `tox`, a Makefile is provided with the
following command:

```sh
$ make flake8
$ make test
$ make coverage
```

## License

[MIT LICENSE](LICENSE).


## Authors

- noamraph (original author)
- JackMc
- arkottke
- obiwanus
- fordhurley
- kmike
- hadim
- casperdcl
