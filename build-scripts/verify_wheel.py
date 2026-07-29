"""Assert an installed pysqlite3 wheel really is the pinned, static build.

setup.py falls back to linking the *system* libsqlite3 whenever sqlite3.c is
absent from the checkout, and that fallback is silent -- the build succeeds and
the wheel imports fine, it just contains whatever SQLite the build host had.
This runs as part of cibuildwheel's test-command so that mistake fails CI
instead of shipping.

Run from any directory other than the checkout root, so that the source
pysqlite3/ package cannot shadow the installed one.
"""
import importlib
import os
import subprocess
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_source import SQLITE_VERSION  # noqa: E402

# Compile options that setup.py asks for and production depends on.
REQUIRED_COMPILE_OPTIONS = ['ENABLE_FTS5', 'ENABLE_RTREE', 'ENABLE_MATH_FUNCTIONS']


def assert_statically_linked(so_path):
    """Fail if the extension has a libsqlite3 dependency.

    The version check above cannot catch this on a host whose system SQLite
    happens to match the pin -- linkage is the only thing that distinguishes
    them there, and a wheel that resolves libsqlite3 at load time is exactly
    what breaks on a machine with an older one.
    """
    if sys.platform == 'darwin':
        cmd = ['otool', '-L', so_path]
    elif sys.platform.startswith('linux'):
        cmd = ['ldd', so_path]
    else:
        print('linkage check skipped on %s' % sys.platform)
        return

    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        print('linkage check skipped (%s unavailable: %s)' % (cmd[0], exc))
        return

    hits = [line.strip() for line in out.splitlines() if 'sqlite3' in line
            and os.path.basename(so_path) not in line]
    if hits:
        raise SystemExit(
            'Extension links libsqlite3 dynamically:\n  %s\nThe amalgamation '
            'was missing at build time, so this wheel is not self-contained.'
            % '\n  '.join(hits))
    print('no dynamic libsqlite3 dependency (%s)' % cmd[0])


def main():
    # `pysqlite3.dbapi2` re-exports the compiled `pysqlite3._sqlite3` through
    # `import *`, and that module sets `sqlite_version`, `connect` and the rest
    # from C (see src/module.c). None of it is visible to a static checker, with
    # or without the built .so present, so pyright reports every access here as
    # an unknown attribute. Binding these as `Any` states that fact where it is
    # true, rather than switching off reportAttributeAccessIssue for the file
    # and losing the check on genuine typos.
    dbapi2: Any = importlib.import_module('pysqlite3.dbapi2')
    ext: Any = importlib.import_module('pysqlite3._sqlite3')

    if os.path.exists(os.path.join(os.getcwd(), 'pysqlite3')):
        raise SystemExit('Refusing to verify from the checkout root: the source '
                         'pysqlite3/ package would shadow the installed wheel.')

    print('imported pysqlite3 from %s' % dbapi2.__file__)

    if dbapi2.sqlite_version != SQLITE_VERSION:
        raise SystemExit(
            'Linked SQLite is %s but the pin is %s.\nThe amalgamation was '
            'probably missing at build time, so this wheel links the build '
            "host's libsqlite3 instead of the pinned static sources."
            % (dbapi2.sqlite_version, SQLITE_VERSION))
    print('linked SQLite %s matches the pin' % dbapi2.sqlite_version)

    assert_statically_linked(ext.__file__)

    conn = dbapi2.connect(':memory:')
    options = {row[0].split('=')[0] for row in
               conn.execute('pragma compile_options')}
    missing = [opt for opt in REQUIRED_COMPILE_OPTIONS if opt not in options]
    if missing:
        raise SystemExit('Wheel is missing compile options: %s'
                         % ', '.join(missing))
    print('compile options present: %s' % ', '.join(REQUIRED_COMPILE_OPTIONS))

    # The reason this fork exists: ALTER TABLE support newer than the SQLite a
    # distro or macOS is likely to supply.
    conn.execute('create table t(a, b, c)')
    conn.execute('alter table t drop column c')
    conn.execute('alter table t rename column b to bb')
    conn.execute('create table s(a int) strict')
    print('ALTER TABLE DROP/RENAME COLUMN and STRICT tables OK')
    conn.close()


if __name__ == '__main__':
    main()
