# HOW TO CONTRIBUTE TO TQDM

**TL;DR: Skip to [QUICK DEV SUMMARY]**

This file describes how to

- contribute changes to the project, and
- upload released to the PyPI repository.

Most of the management commands have been directly placed inside the
Makefile:

```
make [<alias>]  # on UNIX-like environments
python setup.py make [<alias>]  # if make is unavailable
```

The latter depends on [`py-make>=0.1.0`](https://github.com/tqdm/py-make).

Use the alias `help` (or leave blank) to list all available aliases.


## HOW TO COMMIT CONTRIBUTIONS

Contributions to the project are made using the "Fork & Pull" model. The
typical steps would be:

1. create an account on [github](https://github.com)
2. fork [`tqdm`](https://github.com/tqdm/tqdm)
3. make a local clone: `git clone https://github.com/your_account/tqdm.git`
4. make changes on the local copy
5. test (see below) and commit changes `git commit -a -m "my message"`
6. `push` to your GitHub account: `git push origin`
7. create a Pull Request (PR) from your GitHub fork
(go to your fork's webpage and click on "Pull Request."
You can then add a message to describe your proposal.)


## WHAT CODE LAYOUT SHOULD I FOLLOW?

Don't worry too much - maintainers can help reorganise contributions.
However it would be helpful to bear in mind:

- The standard core of `tqdm`, i.e. [`tqdm.std.tqdm`](tqdm/std.py)
    + must have no dependencies apart from pure python built-in standard libraries
    + must have negligible impact on performance
    + should have 100% coverage by unit tests
    + should be appropriately commented
    + should have well-formatted docstrings for functions
        * under 76 chars (incl. initial spaces) to avoid linebreaks in terminal pagers
        * use two spaces between variable name and colon, specify a type, and most likely state that it's optional: `VAR<space><space>:<space>TYPE[, optional]`
        * use [default: ...] for default values of keyword arguments
    + will not break backward compatibility unless there is a very good reason
        * e.g. breaking py26 compatibility purely in favour of readability (such as converting `dict(a=1)` to `{'a': 1}`) is not a good enough reason
    + API changes should be discussed carefully
    + remember, with millions of downloads per month, `tqdm` must be extremely fast and reliable
- Any other kind of change may be included in a (possibly new) submodule
    + submodules are likely single python files under the main [tqdm/](tqdm/) directory
    + submodules extending `tqdm.std.tqdm` or any other module (e.g. [`tqdm.notebook.tqdm`](tqdm/notebook.py), [`tqdm.gui.tqdm`](tqdm/gui.py))
    + CLI wrapper `tqdm.cli`
        * if a newly added `tqdm.std.tqdm` option is not supported by the CLI, append to `tqdm.cli.UNSUPPORTED_OPTS`
    + can implement anything from experimental new features to support for third-party libraries such as `pandas`, `numpy`, etc.
    + submodule maturity
        * alpha: experimental; missing unit tests, comments, and/or feedback; raises `tqdm.TqdmExperimentalWarning`
        * beta: well-used; commented, perhaps still missing tests
        * stable: >10 users; commented, 80% coverage
- `.meta/`
    + A "hidden" folder containing helper utilities not strictly part of the `tqdm` distribution itself


## TESTING

Once again, don't worry too much - tests are automated online, and maintainers
can also help.

To test functionality (such as before submitting a Pull
Request), there are a number of unit tests.

### Standard unit tests

The standard way to run the tests:

- install `tox`
- `cd` to the root of the `tqdm` directory (in the same folder as this file)
- run the following command:

```
[python setup.py] make test
# or:
tox --skip-missing-interpreters
```

This will build the module and run the tests in a virtual environment.
Errors and coverage rates will be output to the console/log. (Ignore missing
interpreters errors - these are due to the local machine missing certain
versions of Python.)

Note: to install all versions of the Python interpreter that are specified
in [tox.ini](https://github.com/tqdm/tqdm/blob/master/tox.ini),
you can use `MiniConda` to install a minimal setup. You must also make sure
that each distribution has an alias to call the Python interpreter:
`python27` for Python 2.7's interpreter, `python32` for Python 3.2's, etc.

### Alternative unit tests with pytest

Alternatively, use `pytest` to run the tests just for the current Python version:

- install test requirements: `[python setup.py] make install_test`
- run the following command:

```
[python setup.py] make alltests
```



# MANAGE A NEW RELEASE

This section is intended for the project's maintainers and describes
how to build and upload a new release. Once again,
`[python setup.py] make [<alias>]` will help.
Also consider `pip install`ing development utilities:
`[python setup.py] make install_build` at a minimum, or a more thorough `conda env create`.


## Pre-commit Hook

It's probably a good idea to use the `pre-commit` (`pip install pre-commit`) helper.

Run `pre-commit install` for convenient local sanity-checking.


## Semantic Versioning

The `tqdm` repository managers should:

- follow the [Semantic Versioning](https://semver.org) convention for tagging


## Checking setup.py

To check that the `setup.py`/`setup.cfg`/`pyproject.toml` file is compliant with PyPI
requirements (e.g. version number; reStructuredText in `README.rst`) use:

```
[python setup.py] make testsetup
```

To upload just metadata (including overwriting mistakenly uploaded metadata)
to PyPI, use:

```
[python setup.py] make pypimeta
```


## Merging Pull Requests

This section describes how to cleanly merge PRs.

### 1 Rebase

From your project repository, merge and test
(replace `pr-branch-name` as appropriate):

```
git fetch origin
git checkout -b pr-branch-name origin/pr-branch-name
git rebase master
```

If there are conflicts:

```
git mergetool
git rebase --continue
```

### 2 Push

Update branch with the rebased history:

```
git push origin pr-branch-name --force
```

Non maintainers can stop here.

Note: NEVER just `git push --force` (this will push all local branches,
overwriting remotes).

### 3 Merge

```
git checkout master
git merge --no-ff pr-branch-name
```

### 4 Test

```
[python setup.py] make alltests
```

### 5 Push to master

```
git push origin master
```


## Building a Release and Uploading to PyPI

Formally publishing requires additional steps: testing and tagging.

### Test

Ensure that all online CI tests have passed.

### Tag

- ensure the version has been tagged.
The tag format is `v{major}.{minor}.{patch}`, for example: `v4.4.1`.
The current commit's tag is used in the version checking process.
If the current commit is not tagged appropriately, the version will
display as `v{major}.{minor}.{patch}.dev{N}+g{commit_hash}`.

### Upload

GitHub Actions (GHA) CI should automatically do this after pushing tags.
Manual instructions are given below in case of failure.

Build `tqdm` into a distributable python package:

```
[python setup.py] make build
```

This will generate several builds in the `dist/` folder. On non-windows
machines the windows `exe` installer may fail to build. This is normal.

Finally, upload everything to PyPI. This can be done easily using the
[twine](https://github.com/pypa/twine) module:

```
[python setup.py] make pypi
```

Also, the new release can (should) be added to GitHub by creating a new
release from the [web interface](https://github.com/tqdm/tqdm/releases);
uploading packages from the `dist/` folder
created by `[python setup.py] make build`.
The [wiki] can be automatically updated with GitHub release notes by
running `make` within the wiki repository.

[wiki]: https://github.com/tqdm/tqdm/wiki

Docker images may be uploaded to <https://hub.docker.com/r/tqdm/tqdm>.
Assuming `docker` is
[installed](https://docs.docker.com/install/linux/docker-ce/ubuntu/):

```
make -B docker
docker login
docker push tqdm/tqdm:latest
docker push tqdm/tqdm:$(docker run -i --rm tqdm/tqdm -v)
```

Snaps may be uploaded to <https://snapcraft.io/tqdm>.
Assuming `snapcraft` is installed (`snap install snapcraft --classic --beta`):

```
make snap
snapcraft login
snapcraft push tqdm*.snap --release stable
```

### Notes

- you can also test on the PyPI test servers `test.pypi.org`
before the real deployment
- in case of a mistake, you can delete an uploaded release on PyPI, but you
cannot re-upload another with the same version number
- in case of a mistake in the metadata on PyPI (e.g. bad README),
updating just the metadata is possible: `[python setup.py] make pypimeta`


## Updating Websites

The most important file is `.readme.rst`, which should always be kept up-to-date
and in sync with the in-line source documentation. This will affect all of the
following:

- `README.rst` (generated by `mkdocs.py` during `make build`)
- The [main repository site](https://github.com/tqdm/tqdm) which automatically
  serves the latest `README.rst` as well as links to all of GitHub's features.
  This is the preferred online referral link for `tqdm`.
- The [PyPI mirror](https://pypi.org/project/tqdm) which automatically
  serves the latest release built from `README.rst` as well as links to past
  releases.
- Many external web crawlers.

Additionally (less maintained), there exists:

- A [wiki] which is publicly editable.
- The [gh-pages project] which is built from the
  [gh-pages branch](https://github.com/tqdm/tqdm/tree/gh-pages), which is
  built using [asv](https://github.com/airspeed-velocity/asv).
- The [gh-pages root] which is built from a separate
  [github.io repo](https://github.com/tqdm/tqdm.github.io).

[gh-pages project]: https://tqdm.github.io/tqdm/
[gh-pages root]: https://tqdm.github.io/


## Helper Bots

There are some helpers in
[.github/workflows](https://github.com/tqdm/tqdm/tree/master/.github/workflows)
to assist with maintenance.

- Comment Bot
    + allows maintainers to write `/tag vM.m.p commit_hash` in an issue/PR to create a tag
- Post Release
    + automatically updates the [wiki]
    + automatically updates the [gh-pages root]
- Benchmark
    + automatically updates the [gh-pages project]


## QUICK DEV SUMMARY

For experienced devs, once happy with local master, follow the steps below.
Much is automated so really it's steps 1-5, then 11(a).

1. test (`[python setup.py] make alltests` or rely on `pre-commit`)
2. `git commit [--amend]  # -m "bump version"`
3. `git push`
4. wait for tests to pass
    a) in case of failure, fix and go back to (1)
5. `git tag vM.m.p && git push --tags` or comment `/tag vM.m.p commit_hash`
6. **`[AUTO:GHA]`** `[python setup.py] make distclean`
7. **`[AUTO:GHA]`** `[python setup.py] make build`
8. **`[AUTO:GHA]`** upload to PyPI. either:
    a) `[python setup.py] make pypi`, or
    b) `twine upload -s -i $(git config user.signingkey) dist/tqdm-*`
9. **`[AUTO:GHA]`** upload to docker hub:
    a) `make -B docker`
    b) `docker push tqdm/tqdm:latest`
    c) `docker push tqdm/tqdm:$(docker run -i --rm tqdm/tqdm -v)`
10. **`[AUTO:GHA]`** upload to snapcraft:
    a) `make snap`, and
    b) `snapcraft push tqdm*.snap --release stable`
11. Wait for GHA to draft a new release on <https://github.com/tqdm/tqdm/releases>
    a) replace the commit history with helpful release notes, and click publish
    b) **`[AUTO:GHA]`** attach `dist/tqdm-*` binaries
       (usually only `*.whl*`)
12. **`[SUB][AUTO:GHA-rel]`** run `make` in the `wiki` submodule to update release notes
13. **`[SUB][AUTO:GHA-rel]`** run `make deploy` in the `docs` submodule to update website
14. **`[SUB][AUTO:GHA-rel]`** accept the automated PR in the `feedstock` submodule to update conda
15. **`[AUTO:GHA-rel]`** update the [gh-pages project] benchmarks
    a) `[python setup.py] make testasvfull`
    b) `asv gh-pages`

Key:

- **`[AUTO:GHA]`**: GitHub Actions CI should automatically do this after `git push --tags` (5)
- **`[AUTO:GHA-rel]`**: GitHub Actions CI should automatically do this after release (11a)
- **`[SUB]`**:  Requires one-time `make submodules` to clone `docs`, `wiki`, and `feedstock`
