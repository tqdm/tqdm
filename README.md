![Logo](logo.png)

# tqdm

[![Build Status](https://travis-ci.org/tqdm/tqdm.svg?branch=master)](https://travis-ci.org/tqdm/tqdm)
[![Coverage Status](https://coveralls.io/repos/tqdm/tqdm/badge.svg)](https://coveralls.io/r/tqdm/tqdm)

Instantly make your loops show a progress meter - just wrap any iterable with "tqdm(iterable)", and you're done !

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
def tqdm(iterable, desc='', total=None,
         leave=False, file=sys.stderr,
         mininterval=0.5, miniters=1):         
    """Get an iterable object, and return an iterator which acts exactly like
    the iterable, but prints a progress meter and updates it every time a
    value is requested.

    Parameters
    ----------
    iterable: iterable        
        Iterable to show progress for.
    desc: str, optional
        A short string, describing the progress, that is added in the beginning
        of the line.
    total : int, optional
        The number of expected iterations. If not given, len(iterable) is used
        if it is defined.
    file : `io.TextIOWrapper` or `io.StringIO`, optional
        A file-like object to output the progress message to. By default,
        sys.stderr is used.
    leave : bool, optional
        If it is False (default), tqdm deletes its traces from screen after 
        it has finished iterating over all elements.
    mininterval : float, optional
        If less than mininterval seconds have passed since the last progress 
        meter update, it is not updated again (default: 0.5).
    miniters : float, optional
        If less than miniters iterations have passed since the last progress 
        meter update, it is not updated again (default: 1).
        
    """

def trange(*args, **kwargs):
    """A shortcut for writing tqdm(xrange)"""
    return tqdm(xrange(*args), **kwargs)
```

## Contributions

During development you may want to use these commands :

```sh
$ make help
Please use make <target> where <target> is one of
    test                 : run tests
    flake8               : run flake8 to check PEP8
    coverage             : run tests and check code coverage
    clean                : clean current repository
```

## License

[MIT LICENSE](LICENSE).


## Authors

- noamraph (original author)
