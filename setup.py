# -*- coding: ISO-8859-1 -*-
# setup.py: the distutils script
#
import os
import re
import setuptools
import shutil
import sys
import tempfile

from distutils import log
from distutils.command.build_ext import build_ext
from setuptools import Extension

# If you need to change anything, it should be enough to change setup.cfg.

PACKAGE_NAME = 'pysqlite3'
VERSION = '0.5.4'

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
    q = '\\"' if sys.platform == 'win32' and sys.version_info < (3, 9) else '"'
    return q + arg + q

define_macros = [('MODULE_NAME', quote_argument(PACKAGE_NAME + '.dbapi2'))]


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

    amalgamation_root = "."
    amalgamation_header = os.path.join(amalgamation_root, 'sqlite3.h')
    amalgamation_source = os.path.join(amalgamation_root, 'sqlite3.c')

    amalgamation_message = ('Sqlite amalgamation not found. Please download '
                            'or build the amalgamation and make sure the '
                            'following files are present in the pysqlite3 '
                            'folder: sqlite3.h, sqlite3.c')

    def check_amalgamation(self):
        if not os.path.exists(self.amalgamation_root):
            os.mkdir(self.amalgamation_root)

        header_exists = os.path.exists(self.amalgamation_header)
        source_exists = os.path.exists(self.amalgamation_source)
        if not header_exists or not source_exists:
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


class FullBuilder(AmalgationLibSqliteBuilder):
    def build_extension(self, ext):
        from urllib.request import urlopen
        import zipfile
        try:
            with urlopen('https://sqlite.org/download.html') as fh:
                html = fh.read().decode('utf8')
        except Exception as exc:
            raise RuntimeError('Could not download Sqlite amalgamation: %s' % exc)

        match = re.search(r'(\d{4}/sqlite-amalgamation-(\d+)\.zip)', html)
        if match is None:
            raise RuntimeError('Could not find Sqlite amalgamation on download page.')
        link, version = match.groups()
        url = 'https://sqlite.org/%s' % link
        with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
            print('Downloading sqlite source code: %s' % url)
            with urlopen(url) as fh:
                shutil.copyfileobj(fh, tmp)
            tmp.seek(0)
            with zipfile.ZipFile(tmp) as zf:
                for path in zf.namelist():
                    filename = os.path.basename(path)
                    if filename not in ('sqlite3.c', 'sqlite3.h'):
                        continue

                    with zf.open(path) as src, \
                            open(os.path.join(self.amalgamation_root, filename), 'wb') as dest:
                        shutil.copyfileobj(src, dest)

        super(FullBuilder, self).build_extension(ext)


def get_setup_args():
    return dict(
        name=PACKAGE_NAME,
        version=VERSION,
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
            "build_static": AmalgationLibSqliteBuilder,
            "build_ext": SystemLibSqliteBuilder,
            "build_full": FullBuilder,
        }
    )


if __name__ == "__main__":
    setuptools.setup(**get_setup_args())
