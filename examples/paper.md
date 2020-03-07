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
 - name: Casper O. da Costa-Luis
   orcid: 0000-0002-7211-1557
   affiliation: 1
 - name: Stephen Karl Larroque
   orcid: 0000-0002-6248-0957
   affiliation: 1
 - name: Martin Zugnoni
   affiliation: 2
 - name: Guangshuo Chen
   affiliation: 2
 - name: Hadrien Mary
   orcid: 0000-0001-8199-5932
   affiliation: 1
 - name: Noam Yorav-Raphael
   affiliation: 2
 - name: Kyle Altendorf
   affiliation: 2
 - name: Ivan Ivanov
   affiliation: 2
 - name: James E. King
   affiliation: 2
 - name: Mikhail Korobov
   affiliation: 7
 - name: Daniel Panteleit
   affiliation: 2
 - name: Matthew D. Pagel
   affiliation: 3
 - name: James Lu
   affiliation: 2
 - name: Hugo van Kemenade
   orcid: 0000-0001-5715-8632
   affiliation: 2
 - name: Igor Ljubuncic
   affiliation: 4
 - name: Adnan Umer
   affiliation: 2
 - name: Johannes Hansen
   affiliation: 2
 - name: Charles Newey
   affiliation: 2
 - name: Veith Röthlingshöfer
   orcid: 0000-0002-1824-3153
   affiliation: 2
 - name: FichteFoll
   affiliation: 2
 - name: Mikhail Dektyarev
   affiliation: 2
 - name: Chung-Kai Hung
   affiliation: 2
 - name: Greg Gandenberger
   affiliation: 2
 - name: Min ho Kim
   affiliation: 2
 - name: Thomas A. Caswell
   affiliation: 2
 - name: Orivej Desh
   affiliation: 2
 - name: Alexander Plavin
   orcid: 0000-0003-2914-8554
   affiliation: 2
 - name: Kuang-che Wu
   affiliation: 5
 - name: zz
   affiliation: 2
 - name: Sepehr Sameni
   affiliation: 2
 - name: David W. H. Swenson
   affiliation: 6
 - name: ReadmeCritic
   affiliation: 2
 - name: stonebig
   affiliation: 2
 - name: Cheng Chen
   affiliation: 2
 - name: Staffan Malmgren
   affiliation: 2
 - name: Sergei Izmailov
   affiliation: 2
 - name: Anurag Pandey
   affiliation: 2
 - name: Peter VandeHaar
   affiliation: 2
 - name: Alex Rothberg
   affiliation: 2
 - name: Carlin MacKenzie
   orcid: 0000-0002-9300-0741
   affiliation: 2
 - name: Edward Betts
   affiliation: 2
 - name: Socialery
   affiliation: 2
 - name: Lev Velykoivanenko
   affiliation: 2
 - name: Dyno Fu
   affiliation: 2
 - name: Jack McCracken
   affiliation: 2
 - name: Jose Tiago Macara Coutinho
   affiliation: 2
 - name: Ford Hurley
   affiliation: 2
 - name: David Bau
   affiliation: 2
 - name: Albert Kottke
   affiliation: 2
 - name: Fabian Dill
   affiliation: 2
 - name: Shirish Pokharel
   affiliation: 2
 - name: tqdm developers
   affiliation: 2
affiliations:
 - name: tqdm maintainers
   index: 1
 - name: Independent (Non-affiliated)
   index: 2
 - name: University of California, Davis
   index: 3
 - name: Snap Advocacy
   index: 4
 - name: Google Inc.
   index: 5
 - name: École Normale Supérieure de Lyon
   index: 6
 - name: Scrapinghub Inc.
   index: 7
date: 16 February 2019
bibliography: paper.bib
---

# Introduction

**`tqdm`** is a progress bar library designed to be fast and extensible. It is
written in Python, though ports in other languages are available. `tqdm` means
**progress** in Arabic (*taqaddum* [@tqdm-ar]) and is an abbreviation for
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

`tqdm` is intended to be used in frontends (giving end users a visual indication
of progress of computations or data transfer). It is also useful for developers
for debugging purposes, both as a profiling tool and also as a way of displaying
logging information of an iterative task (such as error during training of
machine learning algorithms). Due to its ease of use, the library is also an
ideal candidate for inclusion in Python educational courses. For general (not
necessarily Python) purposes, the command-line interface (CLI) mode further
presents a useful tool for CLI users and system administrators monitoring data
flow through pipes.

# Features

Exhaustive documentation may be found on the project's [home
page](https://github.com/tqdm/tqdm/#documentation).

The two basic use cases are within Python code and within a CLI:

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
    * Jupyter Notebook
    * Matplotlib
- Support for custom hooks/callbacks, including:
    * pandas
    * Keras [@keras]

## Command-line Interface (CLI)

A CLI is also provided, where `tqdm` may be used a pipe:

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

# Availability

The package supports both Python versions 2 and 3, and is available for download
via `conda` [@conda], `pip` [@pypi], `snap` [@snapcraft], `docker` [@docker],
and *Zenodo* [@zenodo].
Web-based Jupyter interactive demonstrations are also available
[@notebooks;@binder]

Unit tests are run at least weekly on cloud-based continuous integration
[@travis], with code style and security issues checked on
[Codacy](https://app.codacy.com/project/tqdm/tqdm/dashboard) [@code-review].
Coverage is reported on [Coveralls](https://coveralls.io/github/tqdm/tqdm) and
[Codecov](https://codecov.io/gh/tqdm/tqdm), and performance is monitored against
regression [@asv].

# Impact

As of March 2020, `tqdm` has accumulated over 20 million downloads
[@pypi-downloads], and 595 thousand code inclusions [@tqdm-results]. Dependants
of `tqdm` include 64 thousand repositories [@tqdm-dependents] and 7 thousand
libraries [@lib-io]. `tqdm` has a SourceRank of 24 [@sourcerank], placing it in
the world's top 25 Python packages as of early 2020 [@sourcerank-descending].

The source code of `tqdm` is hosted on GitHub, where it has received over 13
thousand stars [@stars;@stars-hist], and was top trending repository during a
period in December 2015 [@trend-hist]. The documentation has received over 850
thousand hits [@hits], with highest rates during weekdays. Historical reading
rates have also trended upwards at the end of holiday periods. This implies
widespread use in commercial and academic settings.
[OpenHub](https://www.openhub.net/p/tqdm) valuates the work according to the
constructive cost model (COCOMO) as being worth approximately $55,000.

The library has also been used in several textbooks [@miller;@boxel;@nandy] and
peer-reviewed scientific publications
[@stein;@cook;@madhikar;@palmer;@knight;@moriwaki;@jackson].
The [`tqdm` wiki](https://github.com/tqdm/tqdm/wiki) also lists other references
in public media.

# Licence

`tqdm`'s source code is OSS, and all versions are archived at the DOI
[10.5281/zenodo.595120](https://doi.org/10.5281/zenodo.595120). The primary
maintainer [Casper da Costa-Luis](https://github.com/casperdcl) releases
contributions under the terms of the MPLv2.0, while all other contributions are
released under the terms of the MIT licence [@licence].

# References
