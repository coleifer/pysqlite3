pysqlite3-yliu
==============

**Unofficial fork of [coleifer/pysqlite3](https://github.com/coleifer/pysqlite3).**
Not affiliated with the upstream project and not published to PyPI. Wheels are
built here and distributed as GitHub Release assets.  Intended for private 
consumption -- USE AT YOUR OWN RISK.

It packages the SQLite module from CPython as a separately-installable module,
statically linked against a **pinned** SQLite amalgamation, so the SQLite
version is a property of the wheel rather than of whatever the host happens to
have installed.

Currently pinned: **SQLite 3.53.4**.

Why this fork exists
--------------------

* Upstream is in maintenance mode; new development moved to
  [cysqlite](https://github.com/coleifer/cysqlite), which is deliberately *not*
  a drop-in replacement for `sqlite3`.
* `pysqlite3-binary` (the third-party binary redistribution) is unmaintained,
  and shipped Linux x86-64 wheels only.
* We need one SQLite version, statically linked, on both macOS x86-64 (dev) and
  Linux x86-64 (prod), so both sides get the same `ALTER TABLE` support and the
  same query planner.

The distribution is renamed to `pysqlite3-yliu` so pip can never confuse it with
upstream's `pysqlite3`. The **import name is still `pysqlite3`**, so it remains a
drop-in `sqlite3` replacement:

```python
import pysqlite3 as sqlite3
```

Installing
----------

Wheels are attached to each [release](https://github.com/yimingliu/pysqlite3/releases).
Point pip at the release's asset list and let it pick the right wheel for the
platform and Python version:

```
pip install pysqlite3-yliu \
    --find-links https://github.com/yimingliu/pysqlite3/releases/expanded_assets/<tag>
```

In a `requirements.txt`, the same thing without needing a command-line flag:

```
--find-links https://github.com/yimingliu/pysqlite3/releases/expanded_assets/<tag>
pysqlite3-yliu==0.6.0+sqlite.3.53.4
```

If you would rather pin the exact artifact, use the asset URL directly. Note
that this hardcodes the Python version and platform, so it needs updating on a
Python upgrade:

```
pysqlite3-yliu @ https://github.com/yimingliu/pysqlite3/releases/download/<tag>/pysqlite3_yliu-0.6.0+sqlite.3.53.4-cp312-cp312-manylinux_2_28_x86_64.whl
```

To build from source instead, install from git — there is no sdist:

```
pip install git+https://github.com/yimingliu/pysqlite3@<tag>
```

What gets built
---------------

Wheels are produced by [cibuildwheel](https://cibuildwheel.pypa.io/) for:

Nine wheels per release — Python 3.12, 3.13 and 3.14 on three platforms:

| Platform | Wheel tag | Runner |
|---|---|---|
| Linux x86-64 | `manylinux_2_28_x86_64` (glibc 2.28 floor; production runs 2.35) | `ubuntu-latest` |
| macOS x86-64 | `macosx_x86_64` | `macos-15-intel` |
| macOS arm64 | `macosx_11_0_arm64` (Apple Silicon starts at macOS 11) | `macos-latest` |

`archs = ["native"]` means a runner only ever builds wheels for its own
architecture, so **every wheel is tested on hardware of its own arch** — one
matrix leg per platform. Cross-compiling both macOS slices from a single runner
does work (`universal2`, or `x86_64` on an arm64 host), but cibuildwheel can
only skip the tests for a foreign architecture, and untested wheels are what
this matrix exists to avoid. All three are standard GitHub runners, so they are
free on this public repo.

Every wheel is tested in its own environment before release: the full 345-test
suite plus [build-scripts/verify_wheel.py](build-scripts/verify_wheel.py), which
asserts the linked SQLite matches the pin, that there is no dynamic `libsqlite3`
dependency, and that the compile options and newer `ALTER TABLE` forms work.
That last check exists because [setup.py](setup.py) falls back to linking the
system `libsqlite3` whenever `sqlite3.c` is absent, and the fallback is silent.

Bumping the SQLite version
--------------------------

Deliberate, and it is one commit. Check what upstream has:

```
$ python build-scripts/fetch_source.py --check
pinned here:    3.53.4 (2026)
latest upstream: 3.53.4 (2026)

Up to date.
```

If a newer release exists, the command prints the three constants to paste into
[build-scripts/fetch_source.py](build-scripts/fetch_source.py) — version, release
year, and the SHA3-256 published on sqlite.org. Update the `+sqlite.<version>`
local segment of `version` in [pyproject.toml](pyproject.toml) to match, commit,
and tag. Downloads are hash-verified, so a corrupted or substituted archive
fails the build rather than shipping.

Releasing
---------

Push a tag matching `N.N.N` (or `N.N.N-something`). The
[wheels workflow](.github/workflows/wheels.yaml) builds and tests every wheel,
then creates a GitHub Release with them attached. `workflow_dispatch` runs the
same build as a dry run and only uploads workflow artifacts.

Building locally
----------------

```
# Downloads and verifies the pinned sqlite3.c / sqlite3.h into the checkout.
$ python build-scripts/fetch_source.py

$ pip wheel . --no-deps -w wheelhouse
```

Two things to know about local macOS builds:

* **The wheel gets tagged for your macOS version.** Homebrew's Python is built
  with `MACOSX_DEPLOYMENT_TARGET` set to the host OS, and `sysconfig` reads that
  config var rather than the environment, so a wheel built on macOS 26 is tagged
  `macosx_26_0` and will not install on anything older. Exporting
  `MACOSX_DEPLOYMENT_TARGET` alone does not change it; `_PYTHON_HOST_PLATFORM`
  does. CI is unaffected — cibuildwheel uses the python.org interpreters, which
  target 10.13. Use CI for anything you intend to distribute.
* **The system-SQLite build does not work on current macOS.** Apple's SDK
  `sqlite3.h` is built with `SQLITE_OMIT_LOAD_EXTENSION`, while setup.py asks for
  `SQLITE_ENABLE_LOAD_EXTENSION`, so `connection.c` fails to compile under
  clang 15+ ("call to undeclared function `sqlite3_load_extension`"). Fetch the
  amalgamation, or point the build at a Homebrew SQLite with
  `CFLAGS=-I/usr/local/opt/sqlite/include LDFLAGS=-L/usr/local/opt/sqlite/lib`.

To build against the system SQLite deliberately, just leave `sqlite3.c` out of
the checkout — setup.py switches to `-lsqlite3` on its own.

Upstream features
-----------------

Everything upstream provides, unchanged:

* User-defined window functions (requires SQLite >= 3.25)
* Flags and VFS can be specified when opening a connection
* Incremental BLOB I/O, [bpo-24905](https://github.com/python/cpython/pull/271)
* Improved error messages, [bpo-16379](https://github.com/python/cpython/pull/1108)
* Simplified detection of DML statements via `sqlite3_stmt_readonly`
* SQLite native backup API
* Custom busy handler and busy timeout

Compiled with FTS3/4/5, JSON1, RTREE, STAT4, math functions, `load_extension`,
`UPDATE`/`DELETE` `LIMIT`, soundex, URI filenames, covering-index scans,
`SQLITE_MAX_VARIABLE_NUMBER=250000` and a 1 TiB mmap ceiling — see
[setup.py](setup.py) for the full list.
