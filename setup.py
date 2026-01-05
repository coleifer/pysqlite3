# -*- coding: ISO-8859-1 -*-
# setup.py: the distutils script
#
import os

from setuptools import Extension
from setuptools import setup


sources = [os.path.join('src', source)
           for source in ["module.c", "connection.c", "cursor.c", "cache.c",
                          "microprotocols.c", "prepare_protocol.c",
                          "statement.c", "util.c", "row.c", "blob.c"]]
include_dirs = []
libraries = []

if os.path.exists('sqlite3.c') and os.path.exists('sqlite3.h'):
    sources.append('sqlite3.c')
    include_dirs.append('.')
else:
    libraries = ['sqlite3']

extensions = [
    Extension(
        'pysqlite3._sqlite3',
        sources=sources,
        include_dirs=include_dirs,
        define_macros=[
            ('MODULE_NAME', '"pysqlite3.dbapi2"'),
            ('SQLITE_ALLOW_COVERING_INDEX_SCAN', 1),
            ('SQLITE_ENABLE_FTS3', 1),
            ('SQLITE_ENABLE_FTS3_PARENTHESIS', 1),
            ('SQLITE_ENABLE_FTS4', 1),
            ('SQLITE_ENABLE_FTS5', 1),
            ('SQLITE_ENABLE_JSON1', 1),
            ('SQLITE_ENABLE_LOAD_EXTENSION', 1),
            ('SQLITE_ENABLE_MATH_FUNCTIONS', 1),
            ('SQLITE_ENABLE_RTREE', 1),
            ('SQLITE_ENABLE_STAT4', 1),
            ('SQLITE_ENABLE_UPDATE_DELETE_LIMIT', 1),
            ('SQLITE_SOUNDEX', 1),
            ('SQLITE_USE_URI', 1),
            ('SQLITE_TEMP_STORE', 3),
            ('SQLITE_MAX_VARIABLE_NUMBER', 250000),
            ('SQLITE_MAX_MMAP_SIZE', 2**40),
        ],
        libraries=libraries,
    ),
]

setup(ext_modules=extensions)
