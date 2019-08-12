pysqlite3
=========

This library takes the SQLite module from Python 3 and packages it as a
separately-installable module.

This may be useful for creating SQLite modules capable of working with other
versions of SQLite (via the amalgamation option).

Additional features:

* User-defined window functions (requires SQLite >= 3.25)
* Flags and VFS an be specified when opening connection
* Incremental BLOB I/O, [bpo-24905](https://github.com/python/cpython/pull/271)
* Improved error messages, [bpo-16379](https://github.com/python/cpython/pull/1108)
* Simplified detection of DML statements via `sqlite3_stmt_readonly`.
* Sqlite native backup API (also present in standard library 3.7 and newer).

Building with System SQLite
---------------------------

To build `pysqlite3` linked against the system SQLite, run:

```
$ python setup.py build
```

Building a statically-linked library
------------------------------------

To build `pysqlite3` statically-linked against a particular version of SQLite,
you need to obtain the SQLite3 source code and copy `sqlite3.c` and `sqlite3.h`
into the source tree.

```
# Download the latest version of SQLite source code and build the source
# amalgamation files (sqlite3.c and sqlite3.h).
$ wget https://www.sqlite.org/src/tarball/sqlite.tar.gz
$ tar xzf sqlite.tar.gz
$ cd sqlite/
$ ./configure
$ make sqlite3.c

# Copy the sqlite3 amalgamation files into the root of the pysqlite3 checkout
# and run build_static + build:
$ cp sqlite/sqlite3.[ch] pysqlite3/
$ cd pysqlite3
$ python setup.py build_static build
```

You now have a statically-linked, completely self-contained `pysqlite3`.
