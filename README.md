tqdm
====

Instantly make your loops show a progress meter - just wrap any iterable with "tqdm(iterable)", and you're done!

![ScreenShot](https://i.imgur.com/he9Aw5C.gif)

tqdm (read ta<i>qa</i>dum, تقدّم) means "progress" in arabic.

You can also use trange(N) as a shortcut for tqdm(xrange(N))

Here's the doc:

```python
def tqdm(iterable, desc='', total=None, leave=False, mininterval=0.5, miniters=1):
    """
    Get an iterable object, and return an iterator which acts exactly like the
    iterable, but prints a progress meter and updates it every time a value is
    requested.
    'desc' can contain a short string, describing the progress, that is added
    in the beginning of the line.
    'total' can give the number of expected iterations. If not given,
    len(iterable) is used if it is defined.
    If leave is False, tqdm deletes its traces from screen after it has finished
    iterating over all elements.
    If less than mininterval seconds or miniters iterations have passed since
    the last progress meter update, it is not updated again.
    """

def trange(*args, **kwargs):
    """A shortcut for writing tqdm(xrange)"""
    return tqdm(xrange(*args), **kwargs)
```
