# -*- coding: ISO-8859-1 -*-
# setup.py: the distutils script
#
import os
import shutil
import sys
from distutils import log
from distutils.command.build_ext import build_ext
from enum import Enum, auto
from html.parser import HTMLParser
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from zipfile import ZipFile

import setuptools
from setuptools import Extension

# If you need to change anything, it should be enough to change setup.cfg.

PACKAGE_NAME = 'pysqlite3'
SQLITE_VERSION = '3.38.3'

# define sqlite sources
sources = [os.path.join('src', source)
           for source in ["module.c", "connection.c", "cursor.c", "cache.c",
                          "microprotocols.c", "prepare_protocol.c",
                          "statement.c", "util.c", "row.c", "blob.c"]]

# define packages
packages = [PACKAGE_NAME]
EXTENSION_MODULE_NAME = "._sqlite3"

# Work around clang raising hard error for unused arguments
if sys.platform == "darwin":
    os.environ['CFLAGS'] = "-Qunused-arguments"
    log.info("CFLAGS: " + os.environ['CFLAGS'])


def quote_argument(arg):
    q = '\\"' if sys.platform == 'win32' and sys.version_info < (3, 7) else '"'
    return q + arg + q

define_macros = [('MODULE_NAME', quote_argument(PACKAGE_NAME + '.dbapi2'))]


class SqliteVersionParser(HTMLParser):

    class State(Enum):
        NOTHING = auto()
        BEFORE_VERSION_DATE = auto()
        BEFORE_VERSION_STRING = auto()

    def __init__(self, *, convert_charrefs: bool = ...) -> None:
        self.state = self.State.NOTHING
        self.versions = {}
        self.next_date = None
        super().__init__(convert_charrefs=convert_charrefs)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "src/timeline?c" in attrs.get("href"):
            self.state = self.State.BEFORE_VERSION_DATE
        elif tag == "td" and "data-sortkey" in attrs:
            self.state = self.State.BEFORE_VERSION_STRING

    def handle_data(self, data):
        if self.state == self.State.BEFORE_VERSION_DATE:
            self.next_date = data
        elif self.state == self.State.BEFORE_VERSION_STRING:
            assert self.next_date is not None, "Malformed HTML"
            self.versions[data] = self.next_date
            self.next_date = None

    def handle_endtag(self, tag):
        self.state = self.State.NOTHING


class SystemLibSqliteBuilder(build_ext):
    description = "Builds a C extension linking against libsqlite3 library"

    def build_extension(self, ext):
        log.info(self.description)

        # For some reason, when setup.py develop is run, it ignores the
        # configuration in setup.cfg, so we just explicitly add libsqlite3.
        # Oddly, running setup.py build_ext -i (for in-place) works fine and
        # correctly reads the setup.cfg.
        ext.libraries.append('sqlite3')
        build_ext.build_extension(self, ext)


class AmalgationLibSqliteBuilder(build_ext):
    description = "Builds a C extension using a sqlite3 amalgamation"

    amalgamation_root = "build/sqlite3"
    amalgamation_header = os.path.join(amalgamation_root, 'sqlite3.h')
    amalgamation_source = os.path.join(amalgamation_root, 'sqlite3.c')

    amalgamation_message = ('Sqlite amalgamation not found. Please download '
                            'or build the amalgamation and make sure the '
                            'following files are present in the pysqlite3 '
                            'folder: sqlite3.h, sqlite3.c')

    def check_amalgamation(self, downloaded=False):
        if not os.path.exists(self.amalgamation_root):
            os.mkdir(self.amalgamation_root)

        header_exists = os.path.exists(self.amalgamation_header)
        source_exists = os.path.exists(self.amalgamation_source)
        if not header_exists or not source_exists:
            if not downloaded:
                print("Reading version list from SQLite website")
                # History Of SQLite Releases https://www.sqlite.org/chronology.html
                parser = SqliteVersionParser()
                with urlopen("https://www.sqlite.org/chronology.html") as f:
                    parser.feed(f.read().decode("utf-8"))
                assert SQLITE_VERSION in parser.versions, "Invalid SQLite version"

                # For version 3.X.Y the filename encoding is 3XXYY00
                v = [int(i) for i in SQLITE_VERSION.split('.')]
                if len(v) == 3:
                    v.append(0)
                v = tuple(v)
                sqlite_version_string = f"{v[0]}{v[1]:02d}{v[2]:02d}{v[3]:02d}"
                release_year = parser.versions[SQLITE_VERSION][:4]
                url = f"https://www.sqlite.org/{release_year}/sqlite-amalgamation-{sqlite_version_string}.zip"
                with NamedTemporaryFile(suffix=".zip") as tmp:
                    print("Downloading SQLite from", url)
                    with urlopen(url) as f:
                        shutil.copyfileobj(f, tmp)
                    tmp.seek(0)
                    with ZipFile(tmp) as zf:
                        files = zf.namelist()
                        
                        sqlite_c = next(fn for fn in files if fn.endswith("sqlite3.c"))
                        with zf.open(sqlite_c) as src, open(self.amalgamation_source, "wb") as dst:
                            shutil.copyfileobj(src, dst)

                        sqlite_h = next(fn for fn in files if fn.endswith("sqlite3.h"))
                        with zf.open(sqlite_h) as src, open(self.amalgamation_header, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                self.check_amalgamation(downloaded=True)
            else:
                raise RuntimeError(self.amalgamation_message)

    def build_extension(self, ext):
        log.info(self.description)

        # it is responsibility of user to provide amalgamation
        self.check_amalgamation()

        # Feature-ful library.
        features = (
            'ALLOW_COVERING_INDEX_SCAN',
            'ENABLE_FTS3',
            'ENABLE_FTS3_PARENTHESIS',
            'ENABLE_FTS4',
            'ENABLE_FTS5',
            'ENABLE_JSON1',
            'ENABLE_LOAD_EXTENSION',
            'ENABLE_MATH_FUNCTIONS',
            'ENABLE_RTREE',
            'ENABLE_STAT4',
            'ENABLE_UPDATE_DELETE_LIMIT',
            'SOUNDEX',
            'USE_URI',
        )
        for feature in features:
            ext.define_macros.append(('SQLITE_%s' % feature, '1'))

        # Always use memory for temp store.
        ext.define_macros.append(("SQLITE_TEMP_STORE", "3"))

        # Increase the maximum number of "host parameters" which SQLite will accept
        ext.define_macros.append(("SQLITE_MAX_VARIABLE_NUMBER", "250000"))

        # Increase maximum allowed memory-map size to 1TB
        ext.define_macros.append(("SQLITE_MAX_MMAP_SIZE", str(2**40)))

        ext.include_dirs.append(self.amalgamation_root)
        ext.sources.append(os.path.join(self.amalgamation_root, "sqlite3.c"))

        if sys.platform != "win32":
            # Include math library, required for fts5.
            ext.extra_link_args.append("-lm")

        build_ext.build_extension(self, ext)

    def __setattr__(self, k, v):
        # Make sure we don't link against the SQLite
        # library, no matter what setup.cfg says
        if k == "libraries":
            v = None
        self.__dict__[k] = v


def get_setup_args():
    return dict(
        name=PACKAGE_NAME,
        description="DB-API 2.0 interface for Sqlite 3.x",
        long_description='',
        author="Charles Leifer",
        author_email="coleifer@gmail.com",
        license="zlib/libpng",
        platforms="ALL",
        url="https://github.com/coleifer/pysqlite3",
        package_dir={PACKAGE_NAME: "pysqlite3"},
        packages=packages,
        ext_modules=[Extension(
            name=PACKAGE_NAME + EXTENSION_MODULE_NAME,
            sources=sources,
            define_macros=define_macros)
        ],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: zlib/libpng License",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX",
            "Programming Language :: C",
            "Programming Language :: Python",
            "Topic :: Database :: Database Engines/Servers",
            "Topic :: Software Development :: Libraries :: Python Modules"],
        cmdclass={
            "build_ext": AmalgationLibSqliteBuilder,
            "build_dynamic": SystemLibSqliteBuilder
        }
    )


setuptools.setup(**get_setup_args())
