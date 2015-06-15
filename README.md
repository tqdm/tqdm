![Logo](logo.png)

# tqdm

[![Build Status](https://travis-ci.org/tqdm/tqdm.svg?branch=master)](https://travis-ci.org/tqdm/tqdm)
[![Coverage Status](https://coveralls.io/repos/tqdm/tqdm/badge.svg)](https://coveralls.io/r/tqdm/tqdm)

Instantly make your loops show a progress meter - just wrap any iterable with
"tqdm(iterable)", and you're done!

tqdm (read ta<i>qa</i>dum, تقدّم) means "progress" in arabic.

![Screenshot](tqdm.gif)

You can also use trange(N) as a shortcut for tqdm(xrange(N))

## Installation

```sh
pip install tqdm
# or
pip install -e git+https://github.com/tqdm/tqdm.git#egg=master
```

## Documentation

```python
def tqdm(iterable, desc=None, total=None, leave=False, file=sys.stderr,
         ncols=None, mininterval=0.1, miniters=1):
    """
    Decorate an iterable object, returning an iterator which acts exactly
    like the orignal iterable, but prints a dynamically updating
    progressbar.
    
    Parameters
    ----------
    iterable  : iterable
        Iterable to decorate with a progressbar.
    desc  : str, optional
        Prefix for the progressbar.
    total  : int, optional
        The number of expected iterations. If not given, len(iterable) is
        used if possible. As a last resort, only basic progress statistics
        are displayed.
    file  : `io.TextIOWrapper` or `io.StringIO`, optional
        Specifies where to output the progress messages.
    leave  : bool, optional
        if unset, removes all traces of the progressbar upon termination of
        iteration [default: False].
    ncols  : int, optional
        The width of the entire output message. If sepcified, dynamically
        resizes the progress meter [default: None]. The fallback meter
        width is 10.
    mininterval  : float, optional
        Minimum progress update interval, in seconds [default: 0.5].
    miniters  : int, optional
        Minimum progress update interval, in iterations [default: 1].
    
    Returns
    -------
    out  : decorated iterator.
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

Alternatively if you don't want to use `tox`, a Makefile is provided with the following command:

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
