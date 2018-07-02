pysqlite3
=========

This library takes the SQLite module from Python 3.6.4 and packages it as a
separately-installable module.

This may be useful for creating SQLite modules capable of working with other
versions of SQLite (via the amalgamation option).

Additional features:

* Support for user-defined window functions (requires SQLite >= 3.25)
* Support specifying flags when opening connection
* Support specifying VFS when opening connection

Original code (c) Gerhard Häring
