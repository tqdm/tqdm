---
title: '`tqdm`: A Fast, Extensible Progress Meter for Python and CLI'
tags:
 - progressbar
 - progressmeter
 - progress-bar
 - meter
 - rate
 - eta
 - console
 - terminal
 - time
 - progress
 - bar
 - gui
 - python
 - parallel
 - cli
 - utilities
 - shell
 - batch
authors:
 - name: Casper O da Costa-Luis
   orcid: 0000-0002-7211-1557
   affiliation: 1
affiliations:
 - name: "Independent (Non-affiliated)"
   index: 1
date: 16 February 2019
bibliography: paper.bib
---
![](../logo.png)

# Summary

**`tqdm`** is a progress bar library designed to be fast and extensible. It is
written in Python, though ports in other languages are available. `tqdm` means
**progress** in Arabic (*taqadum* [@tqdm-ar]) and is an abbreviation for
**I love you so much** in Spanish (*te quiero demasiado* [@tqdm-es]).

It is a common programming problem to have iterative operations where progress
monitoring is desirable or advantageous. Including statements within a `for` loop to `print` out the current iteration number is a common strategy. However, there are many improvements which could be made in such a scenario:

- preventing excessive printing, such as only displaying every $n$^th^
  iteration;
- displaying iteration rate;
- displaying elapsed and estimated completion times, and
- showing all of the above on one continuously updating line.

Addressing all these issues may well take up more developer time and effort than
the rest of the content of the loop. Any changes to iteration rates or attempts
to re-use the printing logic in a different loop may well result in suboptimal
display rates -- displaying every $n$^th^ iteration may be too (in)frequent --
requiring manual adjustment of $n$ to fix.

`tqdm` addresses all of these problems once and for all, taking advantage of
Pythonic patterns to make it a trivial task to add visually appealing,
customisable progress bars without any significant performance degradation even
in the most demanding of scenarios.

# Features

Exhaustive documentation may be found on the project's [home
page](https://github.com/tqdm/tqdm/#documentation).

The package supports both Python versions 2 and 3, and is available for download
via `conda` [@conda], `pip` [@pypi], `snap` [@snapcraft], and *Zenodo*
[@zenodo].

The two basic use cases are within Python code and within a Command-line
interface:

## Python Iterable Wrapper

`tqdm`'s primary (and original) use is as a wrapper around Python iterables. A
simple case would be:

```python
from tqdm import tqdm
from time import sleep
for i in tqdm(range(100)):
    sleep(0.1)
100%|#########################################| 100/100 [00:10<00:00,  9.95it/s]
```

Supported features include:

- Display customisation via arguments such as `desc`, `postfix` and `bar_format`
- Automatic limiting of display updates to avoid slowing down due to excessive
  iteration rates [@stdout]
- Automatic detection of console width to fill  the display
- Automatic use of Unicode to render smooth-filling progress bars on supported
  terminals
- Support for custom rendering frontends, including:
    * Command-line interface
    * *Jupyter* HTML notebooks
    * `matplotlib`
- Support for custom hooks/callbacks, including:
    * `pandas`
    * `keras` [@keras]

## Command-line Interface

A Command-line interface is also provided, where `tqdm` may be used a pipe:

```sh
 # count lines of text in all *.txt files
$ cat *.txt | wc -l
1075075
 # same but with continuously updating progress information
$ cat *.txt | python3 -m tqdm --unit loc --unit_scale | wc -l
1.08Mloc [00:07, 142kloc/s]
 # same if `total` is known
$ cat *.txt | python3 -m tqdm --unit loc --unit_scale --total 1075075 | wc -l
100%|#####################################| 1.08/1.08M [00:07<00:00,  142kloc/s]
1075075
```

# Popularity

As of January 2019, `tqdm` has received:

- over 20 million downloads [@pypi-downloads];
- over 315 thousand code inclusions [@tqdm-results];
  * over 23 thousand dependent repositories [@tqdm-dependents];
  * 7 thousand dependent libraries [@lib-io];
- a SourceRank of 22 [@sourcerank], in the world's top 20 Python packages as of
  early 2019 [@sourcerank-descending];
- 9 thousand stars on GitHub [@stars;@stars-hist], and the top trending
  repository during a period in December 2015 [@trend-hist];
- 500 thousand documentation hits [@hits];
- usage in several textbooks [@miller;@boxel;@nandy] and peer-reviewed
  scientific publications [@stein;@cook;@madhikar;@palmer;@knight].

## References in Blogs and Public Media

- A `tqdm` release becomes [Zenodo's 1 millionth
  record](https://twitter.com/WikimediaItalia/status/914448810117545985)
- [A Hymn to Progress](http://www.metafilter.com/161265/An-alternative-to-an-eternally-spinning-wheel#6644017),
  a poem or song with suggested tune of *For those in Peril on the C*,
  where "C" is a pun on *Sea* and the *C programming language*
- [My top 5 'new' Python modules of
  2015](http://blog.rtwilson.com/my-top-5-new-python-modules-of-2015/)
- [`tqdm`, `imageio` and `Seaborn`: Three essential python modules
  (Nov 2018)](https://dominikschmidt.xyz/python-modules-tqdm-imageio-seaborn/)
- <https://pythontips.com/2018/06/03/top-14-most-famous-python-libraries-frameworks>
- <https://github.com/IliaGavrilov/Machine_Learning_libraries_and_Python_3.6_tricks>
- <https://github.com/robclewley/TqdmAudioRicker>

## Code Metrics

- Unit tested on cloud-based continuous integration [@travis]
- Style and security checked on
  [Codacy](https://app.codacy.com/project/tqdm/tqdm/dashboard) [@code-review]
- Code coverage reported on [Coveralls](https://coveralls.io/github/tqdm/tqdm)
  and [Codecov](https://codecov.io/gh/tqdm/tqdm)
- Valuated using the COCOMO model by [OpenHub](https://www.openhub.net/p/tqdm)
- Performance tested against regression [@asv]

# Licence

`tqdm`'s source code is OSS, and may be cited using the DOI
[10.5281/zenodo.595120](https://doi.org/10.5281/zenodo.595120). The primary
maintainer [Casper da Costa-Luis](https://github.com/casperdcl) releases
contributions under the terms of the MPLv2.0, while all other contributions are
released under the terms of the MIT licence [@licence].

# See also

- Ports of [`tqdm` in other languages on
  GitHub](https://github.com/search?q=tqdm&type=Repositories)
  * [Official List of Ports](https://tqdm.github.io/ports/)
- [Interactive demonstration of `tqdm` in a Jupyter
  Notebook](https://notebooks.rmotr.com/demo/gh/tqdm/tqdm)

# References
