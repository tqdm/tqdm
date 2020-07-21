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
 - name: Noam Yorav-Raphael
   affiliation: 1
affiliations:
 - name: Independent (Non-affiliated)
   index: 1
date: 16 February 2019
bibliography: paper.bib
---

Contributors:
Matthew Stevens,
Guangshuo Chen,
Hadrien Mary,
Kyle Altendorf,
Mikhail Korobov,
Hugo van Kemenade,
Ivan Ivanov,
Martin Zugnoni,
Matthew D. Pagel,
Daniel Panteleit,
Marcel Bargull,
Min ho Kim,
Jonas Haag,
Greg Gandenberger,
Veith Röthlingshöfer,
Thomas A. Caswell,
Mikhail Dektyarev,
James E. King III,
immerrr,
Michał Górny,
Charles Newey,
Antony Lee,
Johannes Hansen,
ReadmeCritic,
James Lu,
Max Nordlund,
Nishant Rodrigues,
littlezz,
Jesús Cea,
Yaroslav Halchenko,
Gareth Simons,
Sepehr Sameni,
Kuang-che Wu,
David W. H. Swenson,
Alexander Plavin,
William Turner,
Julien Chaumont,
Mike Kutzma,
FichteFoll,
Chung-Kai Hung,
Igor Ljubuncic,
Leonardo Taccari,
Carlin MacKenzie,
Cheng Chen,
stonebig,
Peter VandeHaar,
David Bau,
Robert Krzyzanowski,
Adnan Umer,
Sergei Izmailov,
David Anes,
toddrme2178,
Alex Rothberg,
Orivej Desh,
Staffan Malmgren,
Albert Kottke,
Andrey Portnoy,
Anurag Pandey,
Arun Persaud,
Daniel King,
darindf,
Dyno Fu,
Dénes Türei,
Edward Betts,
Fabian Dill,
Ford Hurley,
Jack McCracken,
Jan Schlüter,
Javi Merino,
Jose Tiago Macara Coutinho,
Josh Karpel,
Lev Velykoivanenko,
Pablo Zivic,
Rafael Lukas Maers,
Riccardo Coccioli,
Shirish Pokharel,
Socialery,
Tomas Ostasevicius,
zed

# Introduction

**`tqdm`** is a progress bar library designed to be fast and extensible. It is
written in Python, though ports in other languages are available. `tqdm` is pronounced
*taqaddum*, meaning **progress** in Arabic [@tqdm-ar].

Program optimization is a pervasive goal in all computing applications:
everybody wants their tasks completed fast. But when this is not possible,
a slow task can be made more ergonomic through progress monitoring.
A common time sink and programming problem is to have iterative operations where progress
monitoring is desirable. Progress monitoring is often implemented as an afterthought,
resulting in a suboptimal overhead and various issues which only adds to the development
time that could be better spent on the core software. A common, but suboptimal, strategy
is to include statements within a `for` loop to `print` out the current iteration number.
However, there are many improvements which could be made in such a scenario:

- preventing expensive I/O access such as excessive printing and time access,
  by a dual memoization of time and iterations (e.g., allowing to display only
  every $n$^th^ iteration);
- use Pythonic structures such as iterables to ease and universalize
  progress meter calls;
- displaying iteration rate, elapsed and estimated completion times;
- showing all of the above on one continuously updating line;
- support hierarchical or parallel tasks, with a progress bar for each.

Addressing all these issues may well take up more developer time and effort than
the rest of the content of the loop. Any changes to iteration rates or attempts
to re-use the printing logic in a different loop may well result in suboptimal
display rates -- displaying every $n$^th^ iteration may be too (in)frequent --
requiring manual adjustment of $n$ to fix. Accomodating a wide range of use cases,
such as hierarchical or parallel tasks, which are common needs, can be highly
challenging and usual implementations tend to scale badly and be too specific
for reuse in other projects.

By modularizing this task in a package dedicated for progress monitoring,
`tqdm` decouples the progress monitoring logic from the core application
and addresses all of these problems once and for all. It takes advantage of
Pythonic patterns to make it a trivial task to add visually appealing,
customisable progress bars without any significant performance degradation even
in the most demanding of scenarios. Performance is unit tested to ensure the
overhead stays negligible, and the modular architecture eases the development of
extensions such as wrappers for Jupyter scientific notebooks.

`tqdm` is intended to be used both in frontends (giving end users a visual indication
of progress of computations or data transfer), or for quick prototyping by developers
for debugging purposes, both as a profiling tool and also as a way of displaying
logging information of an iterative task (such as error during training of
machine learning algorithms), as it can be disabled at runtime with no code change.
Due to its ease of use, the library is also an ideal candidate for inclusion in
Python educational courses. For general (not necessarily Python) purposes, the
command-line interface (CLI) mode further presents a useful tool for CLI users
and system administrators monitoring data flow through pipes.

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
```
```
100%|#########################################| 100/100 [00:10<00:00,  9.95it/s]
```

Unbounded loops are also supported through manual control of `tqdm`:

```python
from tqdm import tqdm
from time import sleep
with tqdm() as pbar:
    while True:
        sleep(0.1)
        pbar.update(1)
```
```
146it [00:14,  9.89it/s]
```

Supported features include:

- Display customisation via arguments such as `desc`, `postfix` and `bar_format`
- Automatic limiting of display updates to avoid slowing down due to excessive
  iteration rates [@stdout]
- Automatic detection of console width to fill  the display
- Automatic use of Unicode to render smooth-filling progress bars on supported
  terminals
- Nested and parallel progress bars
- Anti-freezing background monitor to ensure timely progress updates
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
regression [@asv] and against a minimal loop with and without progress monitoring
to automatically quantify the overhead.

# Impact

As of June 2020, `tqdm` has accumulated over 130 million downloads
[@pypi-downloads], and 962 thousand code inclusions [@tqdm-results]. Dependants
of `tqdm` include 83 thousand repositories [@tqdm-dependents] and 13 thousand
libraries [@lib-io]. `tqdm` has a SourceRank of 24 [@sourcerank], placing it in
the world's top 25 Python packages as of mid 2020 [@sourcerank-descending].

The source code of `tqdm` is hosted on GitHub, where it has received over 14
thousand stars [@stars;@stars-hist], and was top trending repository during a
period in December 2015 [@trend-hist]. The documentation has received over 960
thousand hits [@hits], with highest rates during weekdays. Historical reading
rates have also trended upwards at the end of holiday periods. This implies
widespread use in commercial and academic settings.
[OpenHub](https://www.openhub.net/p/tqdm) valuates the work according to the
constructive cost model (COCOMO) as being worth approximately $57,000.

The library has also been used in several textbooks [@miller;@boxel;@nandy] and
peer-reviewed scientific publications
[@stein;@cook;@madhikar;@palmer;@knight;@moriwaki;@jackson].
The [`tqdm` wiki](https://github.com/tqdm/tqdm/wiki) also lists other references
in public media.

# Licence

`tqdm`'s source code is open-source software (OSS), and all versions are archived
at the DOI [10.5281/zenodo.595120](https://doi.org/10.5281/zenodo.595120). The primary
maintainer [Casper da Costa-Luis](https://github.com/casperdcl) releases
contributions under the terms of the MPLv2.0, while all other contributions are
released under the terms of the MIT licence [@licence].

# Acknowledgements

`tqdm` is the result of the collaborative efforts since October 2013 of a community
of contributors which are listed at the top of the document in order of contributions
according to `git fame -wMC` [@gitfame].
The authors would like to express their gratitude for all the contributions.

# References
